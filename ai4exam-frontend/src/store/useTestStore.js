// src/store/useTestStore.js
import { create } from 'zustand';

const useTestStore = create((set, get) => {
  const resetStreamState = {
    streamMetadata: null,
    streamQuestions: [],
    isStreamLoading: false,
    isStreamCompleted: false,
    streamError: null,
  };

  const processStreamResponse = async (response) => {
    console.log('[STORE] processStreamResponse: Action started.');
    set({ ...resetStreamState, isStreamLoading: true });

    try {
      if (!response || !response.body) throw new Error('Response object or its body is null');

      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = '';

      const processBuffer = () => {
        // 使用 SSE 的标准分隔符 `\n\n` 来切分消息
        const messages = buffer.split('\n\n');

        // 保留最后一个可能不完整的消息，放回缓冲区
        buffer = messages.pop() || '';

        for (const msg of messages) {
          if (msg.startsWith('data:')) {
            const jsonStr = msg.substring(5).trim(); // 移除 "data: " 前缀
            if (jsonStr) {
              try {
                const data = JSON.parse(jsonStr);
                console.log('[STORE] Successfully parsed data chunk:', data);

                if (data.type === 'metadata') {
                  set({ streamMetadata: data.content });
                } else if (data.type === 'question') {
                  console.log('%c[STORE] Adding question to state:', 'color: green; font-weight: bold;', data.content);
                  set(state => ({ streamQuestions: [...state.streamQuestions, data.content] }));
                } else if (data.type === 'end') {
                  console.log('%c[STORE] End signal received!', 'color: red; font-weight: bold;');
                  // 收到结束信号后，提前终止
                  set({ isStreamCompleted: true, isStreamLoading: false });
                  reader.cancel(); // 确保 reader 被关闭
                  return; // 退出处理函数
                }
              } catch (e) {
                console.error('Failed to parse JSON from stream chunk:', jsonStr, e);
              }
            }
          }
        }
      };

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          console.log('[STORE] Stream finished reading (done=true).');
          // 处理缓冲区中可能剩余的最后一部分数据
          processBuffer();
          break;
        }

        buffer += value;
        // 每次收到新数据后都尝试处理一下缓冲区
        processBuffer();
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Streaming failed:', error);
        set({ streamError: error.message, isStreamLoading: false });
      }
    } finally {
      console.log('[STORE] processStreamResponse: Finalizing. Setting loading to false and completed to true.');
      // 确保最终状态是完成
      set(state => ({
        isStreamLoading: false,
        isStreamCompleted: true
      }));
    }
  };

  const reset = () => {
    console.log('[STORE] reset: Full state reset called.');
    set({
      testData: null,
      isLoading: false,
      userAnswers: {},
      gradingResults: null,
      submissionStatus: 'in_progress',
      overallFeedback: null,
      singleQuestionFeedbacks: {},
      resultId: null,
      ...resetStreamState,
    });
  };

  // The rest of the store remains the same...
  return {
    testData: null,
    isLoading: false,
    userAnswers: {},
    gradingResults: null,
    submissionStatus: 'in_progress',
    overallFeedback: null,
    singleQuestionFeedbacks: {},
    resultId: null,
    streamMetadata: null,
    streamQuestions: [],
    isStreamLoading: false,
    isStreamCompleted: false,
    streamError: null,
    setTestData: (data) => set({ testData: data, userAnswers: {}, gradingResults: null, submissionStatus: 'in_progress', overallFeedback: null, singleQuestionFeedbacks: {}, resultId: null }),
    setTestForHistory: (data) => set({ testData: data }),
    setIsLoading: (loading) => set({ isLoading: loading }),
    updateUserAnswer: (questionId, answer) => set((state) => ({ userAnswers: { ...state.userAnswers, [questionId]: answer } })),
    setUserAnswers: (answers) => set({ userAnswers: answers }),
    setGradingResults: (results, resultId) => set((state) => {
      if (!state.testData || !state.testData.questions) return { gradingResults: results, resultId };
      const newQuestions = state.testData.questions.map(q => {
        const result = results.find(r => r.question_id === q.id);
        if (result && result.reference_explanation) return { ...q, reference_explanation: result.reference_explanation };
        return q;
      });
      return { gradingResults: results, resultId, testData: { ...state.testData, questions: newQuestions } };
    }),
    setSubmissionStatus: (status) => set({ submissionStatus: status }),
    setOverallFeedback: (feedback) => set({ overallFeedback: feedback }),
    setSingleQuestionFeedback: (questionId, feedback) => set((state) => ({ singleQuestionFeedbacks: { ...state.singleQuestionFeedbacks, [questionId]: feedback } })),
    processStreamResponse,
    reset,
  };
});

export default useTestStore;