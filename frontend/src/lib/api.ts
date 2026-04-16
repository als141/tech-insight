import type {
  ArticleCreateInput,
  ArticleDetail,
  ArticleListResponse,
  ArticleSummary,
  DashboardBootstrap,
  FilterMetaResponse,
  HealthResponse,
  SearchRequest,
  SearchResponse,
} from "./types";

function getBrowserApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/backend";
}

function getServerApiBaseUrl() {
  return (
    process.env.INTERNAL_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1"
  );
}

async function fetchJson<T>(
  url: string,
  init?: RequestInit & { next?: { revalidate?: number } },
): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json() as Promise<T>;
}

export async function getDashboardBootstrap(): Promise<DashboardBootstrap> {
  const base = getServerApiBaseUrl();

  try {
    const [articles, filters, health] = await Promise.all([
      fetchJson<ArticleListResponse>(`${base}/articles?page=1&page_size=20`, {
        cache: "no-store",
      }),
      fetchJson<FilterMetaResponse>(`${base}/meta/filters`, {
        cache: "no-store",
      }),
      fetchJson<HealthResponse>(`${base}/health`, {
        cache: "no-store",
      }),
    ]);

    return { articles, filters, health };
  } catch {
    return {
      articles: { items: [], total: 0, page: 1, page_size: 20 },
      filters: { categories: [], authors: [] },
      health: null,
    };
  }
}

export async function getArticleDetailById(articleId: number): Promise<ArticleDetail> {
  const base = getServerApiBaseUrl();

  return fetchJson<ArticleDetail>(`${base}/articles/${articleId}`, {
    cache: "no-store",
  });
}

function buildArticleListUrl(params: {
  page: number;
  pageSize: number;
  keyword?: string;
  category?: string[];
  author?: string[];
  sort?: string;
}) {
  const base = getBrowserApiBaseUrl();
  const search = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  });

  if (params.keyword) {
    search.set("keyword", params.keyword);
  }
  if (params.sort) {
    search.set("sort", params.sort);
  }
  params.category?.forEach((value) => search.append("category", value));
  params.author?.forEach((value) => search.append("author", value));
  return `${base}/articles?${search.toString()}`;
}

export function fetchArticles(params: {
  page: number;
  pageSize: number;
  keyword?: string;
  category?: string[];
  author?: string[];
  sort?: string;
}) {
  return fetchJson<ArticleListResponse>(buildArticleListUrl(params));
}

export function fetchArticleDetail(articleId: number) {
  return fetchJson<ArticleDetail>(`${getBrowserApiBaseUrl()}/articles/${articleId}`);
}

export function fetchFilters() {
  return fetchJson<FilterMetaResponse>(`${getBrowserApiBaseUrl()}/meta/filters`);
}

export function fetchHealth() {
  return fetchJson<HealthResponse>(`${getBrowserApiBaseUrl()}/health`);
}

export function searchArticles(payload: SearchRequest) {
  return fetchJson<SearchResponse>(`${getBrowserApiBaseUrl()}/search`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createArticle(payload: ArticleCreateInput) {
  return fetchJson<ArticleSummary>(`${getBrowserApiBaseUrl()}/articles`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateArticle(articleId: number, payload: ArticleCreateInput) {
  return fetchJson<ArticleSummary>(`${getBrowserApiBaseUrl()}/articles/${articleId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteArticle(articleId: number) {
  return fetchJson<void>(`${getBrowserApiBaseUrl()}/articles/${articleId}`, {
    method: "DELETE",
  });
}
