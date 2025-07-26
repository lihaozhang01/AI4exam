// src/store/useTestStore.js
import { create } from 'zustand';


const useTestStore = create((set, get) => ({
  testData: null,
  isLoading: false,
  userAnswers: {},
  gradingResults: null, // 存放批改结果 { question_id: result }
  submissionStatus: 'in_progress', // in_progress, submitted_and_showing_answers
  overallFeedback: null, // 存储整卷的AI反馈
  singleQuestionFeedbacks: {}, // 存储单个问题的AI反馈 { question_id: feedback }
  resultId: null, // 存储当前测试结果的ID

  setTestData: (data) => set({
    testData: data,
    userAnswers: {},
    gradingResults: null, // 生成新试卷时，清空所有旧数据
    submissionStatus: 'in_progress', // 生成新试卷时，重置提交状态为进行中
    overallFeedback: null,
    singleQuestionFeedbacks: {},
    resultId: null,
    resultId: null,
  }),
  setTestForHistory: (data) => set({ testData: data }), // 新增：专为历史记录设置试卷数据，不重置其他状态
  setIsLoading: (loading) => set({ isLoading: loading }),

  updateUserAnswer: (questionId, answer) => {
    set((state) => ({
      userAnswers: {
        ...state.userAnswers,
        [questionId]: answer,
      },
    }));
  },

  setUserAnswers: (answers) => set({ userAnswers: answers }),

  // 更新：保存批改结果，并将论述题的参考答案等信息合并回 testData
  setGradingResults: (results, resultId) => set((state) => {
    const newQuestions = state.testData.questions.map(q => {
      const result = results.find(r => r.question_id === q.id);
      if (result && result.reference_explanation) {
        return { ...q, reference_explanation: result.reference_explanation };
      }
      return q;
    });

    return {
      ...state,
      gradingResults: results,
      resultId: resultId,
      testData: { ...state.testData, questions: newQuestions },
    };
  }),

  setSubmissionStatus: (status) => set({ submissionStatus: status }),

  setOverallFeedback: (feedback) => set({ overallFeedback: feedback }),

  setSingleQuestionFeedback: (questionId, feedback) => set((state) => ({
    singleQuestionFeedbacks: {
      ...state.singleQuestionFeedbacks,
      [questionId]: feedback,
    },
  })),

  // 新增：重置所有状态到初始值
  reset: () => set({
    testData: null,
    isLoading: false,
    userAnswers: {},
    gradingResults: null,
    submissionStatus: 'in_progress', // 重置时也直接设为进行中
    overallFeedback: null,
    singleQuestionFeedbacks: {},
  }),
}));

export default useTestStore;