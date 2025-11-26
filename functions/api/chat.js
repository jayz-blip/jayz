// Cloudflare Pages Function for chat API with CSV data support
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

    // JSON 데이터 로드
    let postsData = [];
    let commentsData = [];
    let indexedData = null;
    
    try {
      // Cloudflare Pages에서는 public 디렉토리의 파일에 접근
      const baseUrl = new URL(request.url);
      const postsResponse = await fetch(`${baseUrl.origin}/data/posts.json`);
      const commentsResponse = await fetch(`${baseUrl.origin}/data/comments.json`);
      const indexedResponse = await fetch(`${baseUrl.origin}/data/indexed.json`);
      
      if (postsResponse.ok) postsData = await postsResponse.json();
      if (commentsResponse.ok) commentsData = await commentsResponse.json();
      if (indexedResponse.ok) indexedData = await indexedResponse.json();
    } catch (e) {
      console.warn('JSON 데이터 로드 실패:', e);
    }

    // 고객사 이름 추출
    let clientName = null;
    if (indexedData && indexedData.client_names) {
      for (const name of indexedData.client_names) {
        if (userMessage.includes(name) || name.includes(userMessage.split(' ')[0])) {
          clientName = name;
          break;
        }
      }
    }

    // 날짜 필터 감지
    const dateKeywords = {
      '오늘': 'today',
      '어제': 'yesterday',
      '이번 주': 'this_week',
      '이번주': 'this_week',
      '지난 주': 'last_week',
      '지난주': 'last_week',
      '이번 달': 'this_month',
      '이번달': 'this_month',
      '지난 달': 'last_month',
      '지난달': 'last_month',
      '최근': 'recent',
    };
    
    let dateFilter = null;
    for (const [keyword, value] of Object.entries(dateKeywords)) {
      if (userMessage.includes(keyword)) {
        dateFilter = value;
        break;
      }
    }

    // 필터링된 게시글 가져오기
    let filteredPosts = postsData;
    
    if (clientName && indexedData && indexedData.clients) {
      filteredPosts = indexedData.clients[clientName] || [];
    }
    
    // 날짜 필터 적용
    if (dateFilter) {
      const now = new Date();
      filteredPosts = filteredPosts.filter(post => {
        if (!post.reg_date) return true;
        const postDate = new Date(post.reg_date);
        
        switch (dateFilter) {
          case 'today':
            return postDate.toDateString() === now.toDateString();
          case 'yesterday':
            const yesterday = new Date(now);
            yesterday.setDate(yesterday.getDate() - 1);
            return postDate.toDateString() === yesterday.toDateString();
          case 'this_week':
            const weekStart = new Date(now);
            weekStart.setDate(weekStart.getDate() - weekStart.getDay());
            return postDate >= weekStart;
          case 'last_week':
            const lastWeekStart = new Date(now);
            lastWeekStart.setDate(lastWeekStart.getDate() - lastWeekStart.getDay() - 7);
            const lastWeekEnd = new Date(now);
            lastWeekEnd.setDate(lastWeekEnd.getDate() - lastWeekEnd.getDay());
            return postDate >= lastWeekStart && postDate < lastWeekEnd;
          case 'this_month':
            return postDate.getMonth() === now.getMonth() && postDate.getFullYear() === now.getFullYear();
          case 'last_month':
            const lastMonth = new Date(now);
            lastMonth.setMonth(lastMonth.getMonth() - 1);
            return postDate.getMonth() === lastMonth.getMonth() && postDate.getFullYear() === lastMonth.getFullYear();
          case 'recent':
            const weekAgo = new Date(now);
            weekAgo.setDate(weekAgo.getDate() - 7);
            return postDate >= weekAgo;
          default:
            return true;
        }
      });
    }

    // 댓글 수 기준으로 정렬 (문제 케이스 우선)
    filteredPosts.sort((a, b) => (b.comm_cnt || 0) - (a.comm_cnt || 0));
    
    // 최대 30개만 선택
    const selectedPosts = filteredPosts.slice(0, 30);

    // 컨텍스트 생성
    let boardContext = '';
    if (selectedPosts.length > 0) {
      boardContext = selectedPosts.map(post => {
        const comments = indexedData && indexedData.comments_by_post 
          ? (indexedData.comments_by_post[post.id] || []) 
          : [];
        const commentsText = comments.length > 0 
          ? `\n댓글 (${comments.length}개): ${comments.map(c => `${c.writer}: ${c.content}`).join(' | ')}`
          : '';
        
        return `[고객사: ${post.name}] 작성자: ${post.writer} | 제목: ${post.subject}\n내용: ${post.content}\n등록일: ${post.reg_date} | 댓글 수: ${post.comm_cnt}${commentsText}`;
      }).join('\n---\n');
    }

    // 담당자 정보 추출
    let responsiblePersonInfo = null;
    if (userMessage.includes('담당자') || userMessage.includes('문의') || userMessage.includes('누구')) {
      if (clientName && indexedData && indexedData.clients && indexedData.clients[clientName]) {
        const clientPosts = indexedData.clients[clientName];
        if (clientPosts.length > 0) {
          // 최근 게시글의 작성자
          const latestPost = clientPosts.sort((a, b) => 
            new Date(b.reg_date || 0) - new Date(a.reg_date || 0)
          )[0];
          responsiblePersonInfo = {
            name: latestPost.writer,
            last_activity: latestPost.reg_date
          };
        }
      }
    }

    // 문제 케이스 감지
    const isProblemQuery = ['문제', '어려움', '이슈', '오류', '에러', '장애'].some(
      keyword => userMessage.includes(keyword)
    );

    // 시스템 프롬프트 생성
    let systemPrompt = `당신은 사내 업무를 도와주는 AI 어시스턴트입니다. 
CSV 데이터를 참고하여 정확하고 도움이 되는 답변을 제공하세요.
게시판 정보가 제공된 경우, 그 정보를 바탕으로 답변하되, 
정보가 없는 경우 일반적인 업무 지식으로 답변하세요.
답변은 한국어로 작성하세요.

중요한 지침:
1. 게시글의 작성자 정보가 있는 경우, 답변에 반드시 작성자 이름을 포함하세요. 
   예: "박선미과장님이 이렇게 답변을 해주었다"와 같이 작성자 이름을 명시하세요.
2. 덧글 정보가 있는 경우, 덧글 작성자와 내용을 함께 언급하세요.`;

    if (isProblemQuery) {
      systemPrompt += `
3. 문제나 어려운 케이스에 대한 질문일 때는, 비슷한 기간 내의 게시글 중에서 
   덧글 수가 많은 게시글을 우선적으로 참고하여 답변하세요.`;
    }

    if (responsiblePersonInfo) {
      systemPrompt += `
4. 담당자 문의에 대한 답변:
   - 최근 담당자: ${responsiblePersonInfo.name}
   - 최근 활동일: ${responsiblePersonInfo.last_activity}
   위 정보를 바탕으로 해당 카테고리/업체에 대한 담당자를 안내하세요.`;
    }

    if (boardContext) {
      systemPrompt += `\n\n[사내 게시판 정보]\n${boardContext.substring(0, 3000)}\n\n위 정보를 참고하여 답변하세요.`;
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
            content: systemPrompt
          },
          {
            role: 'user',
            content: userMessage
          }
        ],
        temperature: 0.7,
        max_tokens: 1000
      })
    });

    if (!openaiResponse.ok) {
      const errorData = await openaiResponse.json();
      throw new Error(errorData.error?.message || 'OpenAI API 오류');
    }

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
    console.error('Chat API 오류:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}
