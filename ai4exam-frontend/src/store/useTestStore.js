// src/store/useTestStore.js
import { create } from 'zustand';


const useTestStore = create((set) => ({
  testData: null,
  isLoading: false,
  userAnswers: {},
  gradingResults: null, // 存放批改结果 { question_id: result }
  submissionStatus: 'in_progress', // in_progress, submitted_and_showing_answers
  overallFeedback: null, // 存储整卷的AI反馈
  singleQuestionFeedbacks: {}, // 存储单个问题的AI反馈 { question_id: feedback }

  setTestData: (data) => set({
    testData: data,
    userAnswers: {},
    gradingResults: null, // 生成新试卷时，清空所有旧数据
    submissionStatus: 'in_progress', // 生成新试卷时，重置提交状态为进行中
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
    submissionStatus: 'in_progress', // 重置时也直接设为进行中
    overallFeedback: null,
    singleQuestionFeedbacks: {},
  }),
}));

export default useTestStore;