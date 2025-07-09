// src/store/useTestStore.js
import { create } from 'zustand';

const useTestStore = create((set) => ({
  testData: null,
  isLoading: false,
  userAnswers: {},
  gradingResults: null, // 新增：存放批改结果 { question_id: result }

  setTestData: (data) => set({
    testData: data,
    userAnswers: {},
    gradingResults: null // 生成新试卷时，清空所有旧数据
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

  // 新增：保存批改结果
  setGradingResults: (results) => set({ gradingResults: results }),
}));

export default useTestStore;