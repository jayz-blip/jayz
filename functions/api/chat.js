// Cloudflare Pages Function for chat API
export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    const data = await request.json();
    const userMessage = data.message || '';

    if (!userMessage) {
      return new Response(
        JSON.stringify({ error: '메시지가 필요합니다.' }),
        { 
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }

    // OpenAI API 호출
    const openaiResponse = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${env.OPENAI_API_KEY}`
      },
      body: JSON.stringify({
        model: 'gpt-4',
        messages: [
          {
            role: 'system',
            content: '당신은 사내 업무를 도와주는 AI 어시스턴트입니다.'
          },
          {
            role: 'user',
            content: userMessage
          }
        ]
      })
    });

    const openaiData = await openaiResponse.json();
    const response = openaiData.choices[0]?.message?.content || '응답을 생성할 수 없습니다.';

    return new Response(
      JSON.stringify({
        response: response,
        success: true
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}
