// api/save.js — Vercel 서버리스 함수
// POST /api/save  (PRD 기준 P1: 실제 Notion/Google 저장은 추후, MVP에서는 공유 링크만 제공)
// body: { text, user_name, user_speaker, meeting_date }
//
// MVP에서는 외부 저장 연동 없이, 추출 결과를 보관·재공유할 수 있는 공유 링크를
// 제공하는 것으로 대체한다. (실제 저장은 추후 P1)

export async function POST(request) {
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(
      JSON.stringify({ detail: "유효하지 않은 요청" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  const { text, user_name, user_speaker, meeting_date } = body;

  if (!text || typeof text !== "string") {
    return new Response(
      JSON.stringify({ detail: "text가 필요합니다" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  // 공유 링크는 이 서비스 URL을 공유하는 것으로 MVP 대체.
  // 실제 저장소 저장은 P1에서 구현.
  const sharePayload = {
    text,
    user_name: user_name || "없음",
    user_speaker: user_speaker || "unknown",
    meeting_date: meeting_date || null,
    created_at: new Date().toISOString(),
  };

  // MVP에서는 이렇게 단순 공유 URL을 내려준다.
  // (실제 서비스 도메인 + /share?... 형태는 배포 후 도메인 확정 시 조정)
  const encoded = Buffer.from(JSON.stringify(sharePayload)).toString("base64url");
  const url = `/share?data=${encoded}`;

  return new Response(
    JSON.stringify({
      success: true,
      share_url: url,
      message: "MVP 단계에서는 외부 저장 연동 전입니다. 공유 링크만 제공됩니다.",
    }),
    { headers: { "Content-Type": "application/json" } }
  );
}
