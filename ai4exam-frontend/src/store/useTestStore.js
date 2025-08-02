// src/store/useTestStore.js
import { create } from 'zustand';

// [无需修改] 诊断日志中间件
const log = (config) => (set, get, api) => config((args) => {
  set(args);
}, get, api);


const useTestStore = create(log((set, get) => {
  // ... 其他代码保持不变 ...
  const resetStreamState = {
    streamMetadata: null,
    streamQuestions: [],
    isStreamLoading: false,
    isStreamCompleted: false,
    streamError: null,
  };

  const processStreamResponse = async (response) => {
    
    set({ ...resetStreamState, isStreamLoading: true });

    try {
      if (!response || !response.body) throw new Error('Response object or its body is null');

      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = '';

      const processBuffer = () => {
        const messages = buffer.split('\n\n');
        buffer = messages.pop() || '';

        for (const msg of messages) {
          if (msg.startsWith('data:')) {
            const jsonStr = msg.substring(5).trim();
            if (jsonStr) {
              try {
                const data = JSON.parse(jsonStr);

                if (data.type === 'metadata') {
                  set({ streamMetadata: data.content });
                } else if (data.type === 'question') {
                  set(state => ({ streamQuestions: [...state.streamQuestions, data.content] }));
                } else if (data.type === 'end') {
                  set({ isStreamCompleted: true, isStreamLoading: false });
                  reader.cancel();
                  return;
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
          processBuffer();
          break;
        }

        buffer += value;
        processBuffer();
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Streaming failed:', error);
        set({ streamError: error.message, isStreamLoading: false });
      }
    } finally {
      console.log('[STORE] processStreamResponse: Finalizing. Setting loading to false and completed to true.');
      set(state => ({
        isStreamLoading: false,
        isStreamCompleted: true
      }));
    }
  };

  const reset = () => {
    // ... 此函数内部代码保持不变 ...
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

  return {
    // ... 其他 state 属性保持不变 ...
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
    setTestData: (data) => set({ testData: data, gradingResults: null, submissionStatus: 'in_progress', overallFeedback: null, singleQuestionFeedbacks: {}, resultId: null }),
    setTestForHistory: (data) => set({ testData: data }),
    setIsLoading: (loading) => set({ isLoading: loading }),
    updateUserAnswer: (questionId, answer) => set((state) => ({ userAnswers: { ...state.userAnswers, [questionId]: answer } })),

    // ===================================================================
    // [核心修改] 在这里增加日志来追踪调用者
    setUserAnswers: (answers) => {
      // 当 setUserAnswers 被调用时，打印传入的答案
      console.warn('setUserAnswers was called! The provided answers are:', answers);
      // 打印一个调用堆栈，告诉我们是哪个文件、哪一行代码调用了它
      console.trace("Trace for setUserAnswers");
      set({ userAnswers: answers });
    },
    // ===================================================================

    setGradingResults: (results, resultId) => set((state) => {
      if (!state.testData || !state.testData.questions) return { gradingResults: results || [], resultId };
      const safeResults = results || [];
      const newQuestions = (state.testData.questions || []).map(q => {
        const result = safeResults.find(r => r.question_id === q.id);
        if (result && result.reference_explanation) return { ...q, reference_explanation: result.reference_explanation };
        return q;
      });
      return { gradingResults: safeResults, resultId, testData: { ...state.testData, questions: newQuestions } };
    }),
    setSubmissionStatus: (status) => set({ submissionStatus: status }),
    setOverallFeedback: (feedback) => set({ overallFeedback: feedback }),
    setSingleQuestionFeedback: (questionId, feedback) => set((state) => ({ singleQuestionFeedbacks: { ...state.singleQuestionFeedbacks, [questionId]: feedback } })),
    processStreamResponse,
    reset,
  };
}));

export default useTestStore;