// api/extract.js — Vercel 서버리스 함수
// POST /api/extract
// body: { text, user_name, user_speaker, meeting_date }
// Solar Pro 4 (Upstage, OpenAI 호환) 호출 → JSON 파싱 → 정규화

const UPSTAGE_API_KEY = process.env.UPSTAGE_API_KEY || "";
const UPSTAGE_BASE_URL = process.env.UPSTAGE_BASE_URL || "https://api.upstage.ai/v1";
const SOLAR_MODEL = process.env.SOLAR_MODEL || "solar-pro4";

const SYSTEM_PROMPT_TEMPLATE = `너는 회의 녹취록에서 특정 참석자 한 명의 액션아이템만 골라내는 추출기다.
반드시 아래 JSON 스키마만 출력한다. 설명, 마크다운, 코드펜스 금지.

[입력 정보]
- 대상자 이름: {user_name}
- 대상자의 화자 라벨: {user_speaker}
- 대상자 소속 부서: {user_dept}
- 회의 날짜: {meeting_date}
- 참석자 목록: {attendees}

[판단 규칙 — 우선순위 순]
1. name_direct_mention : 대상자 이름이 직접 호명되어 업무가 지시·요청됨 → confidence "high"
2. self_speech         : 대상자 화자 라벨이 "제가 하겠습니다/할게요" 등으로 직접 맡음 → "high"
3. department_mention  : 대상자 부서만 언급됨 (개인 특정 안 됨) → "mid"
4. task_content_match  : 대상자의 업무 영역과 내용이 겹치지만 담당 언급 없음 → "low"
5. ambiguous           : 담당자가 불명확 → "low"
- 다른 사람 이름이 담당자로 명시된 항목은 절대 포함하지 않는다.
- 결정·정보 공유·잡담은 할 일이 아니다. 실행 행동만 추출한다.
- 같은 할 일이 반복 언급되면 하나로 합치고 highlights에 근거를 모두 담는다.
- 대상자 이름이 "없음"이면 name_direct_mention과 self_speech는 사용할 수 없다.

[근거 규칙]
- highlights.snippet은 원문에서 한 글자도 바꾸지 않고 그대로 복사한다.
- start_index/end_index는 자신 없으면 0으로 둔다. snippet 정확성이 우선이다.

[마감일 규칙]
- due_expression : 원문의 기한 표현 그대로. 없으면 null.
- due_clarity    : 절대 날짜면 "absolute", 상대 표현이면 "relative", 없으면 "unclear".
- due_date       : "absolute"일 때만 YYYY-MM-DD, 그 외 null. 상대 표현을 네가 계산하지 마라.

[출력 스키마]
{
  "tasks": [
    {
      "text": "할 일을 한 문장으로 (대상자 기준, 동사형)",
      "confidence": "high|mid|low",
      "assignee_rationale": "name_direct_mention|self_speech|department_mention|task_content_match|ambiguous",
      "assignee_name": "대상자 이름 또는 null",
      "highlights": [{"snippet": "...", "start_index": 0, "end_index": 0}],
      "due_expression": "... 또는 null",
      "due_clarity": "absolute|relative|unclear",
      "due_date": "YYYY-MM-DD 또는 null"
    }
  ],
  "attendee_names_mentioned": ["녹취록에서 언급된 사람 이름들"]
}
할 일이 없으면 {"tasks": [], "attendee_names_mentioned": []} 를 출력한다.`;

function buildSystemPrompt(params) {
  return SYSTEM_PROMPT_TEMPLATE
    .replace("{user_name}", params.user_name)
    .replace("{user_speaker}", params.user_speaker)
    .replace("{user_dept}", params.user_dept)
    .replace("{meeting_date}", params.meeting_date)
    .replace("{attendees}", params.attendees);
}

function removeCodeFence(content) {
  const cleaned = content.trim();
  const fenceMatch = cleaned.match(/^```(?:json)?\s*\n?(.*?)```\s*$/s);
  if (fenceMatch) return fenceMatch[1].trim();
  return cleaned;
}

function parseJsonContent(content) {
  const cleaned = removeCodeFence(content);
  return JSON.parse(cleaned);
}

function normalizeSolarResult(raw) {
  if (!raw || typeof raw !== "object") {
    return { tasks: [], attendee_names_mentioned: [] };
  }

  const tasks = Array.isArray(raw.tasks) ? raw.tasks : [];
  const attendee_names_mentioned = Array.isArray(raw.attendee_names_mentioned)
    ? raw.attendee_names_mentioned
    : [];

  const normalizedTasks = tasks.map((t) => ({
    text: (t.text || "").toString(),
    confidence: ["high", "mid", "low"].includes(t.confidence) ? t.confidence : "low",
    assignee_rationale: [
      "name_direct_mention",
      "self_speech",
      "department_mention",
      "task_content_match",
      "ambiguous",
    ].includes(t.assignee_rationale)
      ? t.assignee_rationale
      : "ambiguous",
    assignee_name: t.assignee_name || null,
    highlights: Array.isArray(t.highlights)
      ? t.highlights.map((h) => ({
          snippet: (h.snippet || "").toString(),
          start_index: Number(h.start_index) || 0,
          end_index: Number(h.end_index) || 0,
        }))
      : [],
    due_expression: t.due_expression || null,
    due_clarity: ["absolute", "relative", "unclear"].includes(t.due_clarity)
      ? t.due_clarity
      : "unclear",
    due_date: t.due_date || null,
  }));

  return {
    tasks: normalizedTasks,
    attendee_names_mentioned,
  };
}

export async function POST(request) {
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(
      JSON.stringify({ detail: "유효하지 않은 요청" }),
      {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  const { text, user_name, user_speaker, meeting_date } = body;

  if (!text || typeof text !== "string") {
    return new Response(
      JSON.stringify({ detail: "text가 필요합니다" }),
      {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  if (!UPSTAGE_API_KEY) {
    console.error("UPSTAGE_API_KEY가 설정되지 않았습니다");
    return new Response(
      JSON.stringify({ detail: "Solar Pro 4 API 키가 설정되지 않았습니다" }),
      {
        status: 502,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  const user = {
    user_name: user_name || "없음",
    user_speaker: user_speaker || "unknown",
    user_dept: "",
    meeting_date: meeting_date || "",
    attendees: [],
  };

  const systemPrompt = buildSystemPrompt(user);
  const prompt = `[녹취록]\n${text}`;

  const payload = {
    model: SOLAR_MODEL,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: prompt },
    ],
    temperature: 0,
    response_format: { type: "json_object" },
  };

  console.log(`[Solar 요청] model=${SOLAR_MODEL}, prompt_length=${prompt.length}`);

  let response;
  try {
    response = await fetch(`${UPSTAGE_BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${UPSTAGE_API_KEY}`,
      },
      body: JSON.stringify(payload),
    });
  } catch (e) {
    console.error("Solar Pro 4 호출 중 네트워크 오류:", e);
    return new Response(
      JSON.stringify({ detail: "Solar Pro 4 호출 실패: 네트워크 오류" }),
      {
        status: 502,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  if (!response.ok) {
    const errorText = await response.text().catch(() => "");
    console.error(
      `Solar Pro 4 API 오류: status=${response.status}, body=${errorText.slice(0, 500)}`
    );
    return new Response(
      JSON.stringify({ detail: `Solar Pro 4 API 오류: ${response.status}` }),
      {
        status: 502,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content;
  if (!content) {
    console.error("Solar 응답에서 content를 찾을 수 없습니다:", JSON.stringify(data).slice(0, 500));
    return new Response(
      JSON.stringify({ detail: "Solar 응답에서 content를 찾을 수 없습니다" }),
      {
        status: 502,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  console.log(`[Solar 응답] content_length=${content.length}`);

  let parsed;
  try {
    parsed = parseJsonContent(content);
  } catch (e) {
    const cleaned = removeCodeFence(content);
    try {
      parsed = JSON.parse(cleaned);
    } catch (e2) {
      console.error("Solar 응답 JSON 파싱 실패:", content.slice(0, 500));
      return new Response(
        JSON.stringify({ detail: "Solar 응답 JSON 파싱 실패" }),
        {
          status: 502,
          headers: { "Content-Type": "application/json" },
        }
      );
    }
  }

  const result = normalizeSolarResult(parsed);
  return new Response(JSON.stringify(result), {
    headers: { "Content-Type": "application/json" },
  });
}
