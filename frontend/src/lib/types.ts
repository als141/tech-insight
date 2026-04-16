export type ArticleSummary = {
  id: number;
  title: string;
  content: string;
  author: string;
  category: string;
  published_at: string;
  created_at: string;
  updated_at: string;
};

export type ArticleVariant = {
  id: number;
  title: string;
  author: string;
  category: string;
  published_at: string;
};

export type ArticleDetail = ArticleSummary & {
  duplicate_count: number;
  variants: ArticleVariant[];
  related_articles: ArticleVariant[];
};

export type ArticleCreateInput = {
  title: string;
  content: string;
  author: string;
  category: string;
  published_at: string;
};

export type ArticleListResponse = {
  items: ArticleSummary[];
  total: number;
  page: number;
  page_size: number;
};

export type SearchFilters = {
  category: string[];
  author: string[];
  publishedFrom: string | null;
  publishedTo: string | null;
};

export type SearchRequest = {
  query: string;
  mode: "keyword" | "semantic" | "hybrid";
  filters: SearchFilters;
  sort: "relevance" | "newest" | "oldest";
  includeDuplicates: boolean;
  page: number;
  pageSize: number;
};

export type SearchItem = {
  articleId: number;
  title: string;
  author: string;
  category: string;
  contentPreview: string;
  publishedAt: string;
  semanticScore: number;
  keywordScore: number;
  finalScore: number;
  duplicateCount: number;
  matchedBy: string[];
};

export type SearchResponse = {
  items: SearchItem[];
  total: number;
};

export type FilterMetaResponse = {
  categories: string[];
  authors: string[];
};

export type HealthResponse = {
  status: string;
  database: string;
  embeddingProvider: string;
  embeddingModel: string;
};

export type DashboardBootstrap = {
  articles: ArticleListResponse;
  filters: FilterMetaResponse;
  health: HealthResponse | null;
};
