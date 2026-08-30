import { defineStore } from 'pinia'
import axios from 'axios'
import { apiConfig } from '../../config/api'

export const useNewsStore = defineStore('news', {
  state: () => ({
    newsList: [],
    newsDetail: {},
    categories: [],
    currentCategory: 1,
    loading: false,
    refreshing: false,
    finished: false,
    categoriesLoading: false
  }),

  actions: {
    // 获取新闻分类
    async getCategories() {
      if (this.categoriesLoading) return;

      this.categoriesLoading = true;

      try {
        const response = await axios.get(`${apiConfig.baseURL}/api/news/categories`);

        if (response.data && response.data.code === 200) {
          this.categories = [...response.data.data, { id: 10, name: '更多' }];

          // 如果没有设置当前分类，则设置为第一个分类
          if (!this.currentCategory && this.categories.length > 0) {
            this.currentCategory = this.categories[0].id;
          }
        }
      } catch (error) {
        console.error('获取新闻分类失败:', error);
        // API 请求失败时使用默认分类兜底
        this.categories = [
          { id: 1, name: '头条' },
          { id: 2, name: '社会' },
          { id: 3, name: '国内' },
          { id: 4, name: '国际' },
          { id: 5, name: '娱乐' },
          { id: 6, name: '体育' },
          { id: 7, name: '科技' }
        ];
      } finally {
        this.categoriesLoading = false;
      }
    },

    // 切换新闻分类
    changeCategory(categoryId) {
      if (this.currentCategory !== categoryId) {
        this.currentCategory = categoryId
        this.newsList = []
        this.finished = false
        this.getNewsList(true)
      }
    },

    // 获取新闻列表（分页加载）
    async getNewsList(isRefresh = false) {
      if (isRefresh) {
        this.refreshing = true
        this.newsList = []
        this.finished = false
      }

      this.loading = true

      try {
        const params = {
          categoryId: this.currentCategory,
          page: isRefresh ? 1 : Math.ceil(this.newsList.length / 10) + 1,
          pageSize: 10
        }

        const response = await axios.get(`${apiConfig.baseURL}/api/news/list`, { params });

        if (response.data && response.data.code === 200) {
          const newsData = response.data.data.list;

          this.newsList = isRefresh ? newsData : [...this.newsList, ...newsData];

          if (newsData.length < params.pageSize) {
            this.finished = true;
          }
        }
      } catch (error) {
        console.error('获取新闻列表失败:', error)
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },

    // 获取新闻详情
    async getNewsDetail(id) {
      try {
        const response = await axios.get(`${apiConfig.baseURL}/api/news/detail?id=${id}`);

        if (response.data && response.data.code === 200) {
          this.newsDetail = response.data.data;
        } else {
          console.error('获取新闻详情失败: 接口返回错误');
        }
      } catch (error) {
        console.error('获取新闻详情失败:', error);
      }
    }
  }
})
