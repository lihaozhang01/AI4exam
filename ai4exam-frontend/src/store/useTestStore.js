// src/store/useTestStore.js
import { create } from 'zustand';


const useTestStore = create((set) => ({
  testData: null,
  isLoading: false,
  userAnswers: {},
  gradingResults: null, // 存放批改结果 { question_id: result }
  submissionStatus: 'not_submitted', // not_submitted, submitted_and_showing_answers
  overallFeedback: null, // 存储整卷的AI反馈
  singleQuestionFeedbacks: {}, // 存储单个问题的AI反馈 { question_id: feedback }

  setTestData: (data) => set({
    testData: data,
    userAnswers: {},
    gradingResults: null, // 生成新试卷时，清空所有旧数据
    submissionStatus: 'not_submitted', // 生成新试卷时，重置提交状态
    overallFeedback: null,
    singleQuestionFeedbacks: {},
  }),
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

  // 新增：保存批改结果
  setGradingResults: (results) => set({ gradingResults: results }),

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
    submissionStatus: 'not_submitted',
    overallFeedback: null,
    singleQuestionFeedbacks: {},
  }),
}));

export default useTestStore;