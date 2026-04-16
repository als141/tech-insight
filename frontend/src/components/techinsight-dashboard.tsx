"use client";

import { useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Pencil,
  Plus,
  Search,
  Trash2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

import {
  createArticle,
  deleteArticle,
  fetchArticleDetail,
  fetchArticles,
  fetchFilters,
  searchArticles,
  updateArticle,
} from "../lib/api";
import { buildArticlePath } from "../lib/article-path";
import type {
  ArticleSummary,
  DashboardBootstrap,
  SearchRequest,
  SearchResponse,
} from "../lib/types";
import { ArticleFormDialog } from "./article-form-dialog";

function formatDate(value: string) {
  return value.slice(0, 10);
}

type TableRowItem = {
  id: number;
  title: string;
  author: string;
  category: string;
  publishedAt: string;
  source: "list" | "search";
  score: number | null;
  matchedBy: string[];
  duplicateCount: number;
  raw?: ArticleSummary;
};

const MODE_LABELS: Record<SearchRequest["mode"], string> = {
  keyword: "キーワード",
  semantic: "意味検索",
  hybrid: "ハイブリッド",
};

const SORT_LABELS: Record<SearchRequest["sort"], string> = {
  relevance: "関連順",
  newest: "新しい順",
  oldest: "古い順",
};

const LIST_SORT_LABELS = {
  newest: "新しい順",
  oldest: "古い順",
} satisfies Record<"newest" | "oldest", string>;

function buildRowFromArticle(article: ArticleSummary): TableRowItem {
  return {
    id: article.id,
    title: article.title,
    author: article.author,
    category: article.category,
    publishedAt: article.published_at,
    source: "list",
    score: null,
    matchedBy: [],
    duplicateCount: 0,
    raw: article,
  };
}

function buildRowsFromSearch(response: SearchResponse): TableRowItem[] {
  return response.items.map((item) => ({
    id: item.articleId,
    title: item.title,
    author: item.author,
    category: item.category,
    publishedAt: item.publishedAt,
    source: "search",
    score: item.finalScore,
    matchedBy: item.matchedBy,
    duplicateCount: item.duplicateCount,
  }));
}

function FilterDropdown({
  label,
  items,
  selected,
  onToggle,
}: {
  label: string;
  items: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  const summary =
    selected.length === 0
      ? label
      : selected.length === 1
        ? selected[0]
        : `${selected.length}件選択`;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className="h-10 min-w-36 justify-between rounded-full border-slate-300 bg-white px-4"
        >
          <span className="truncate">{summary}</span>
          <ChevronDown className="size-4 text-slate-400" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56 rounded-2xl">
        <DropdownMenuLabel>{label}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {items.map((item) => (
          <DropdownMenuCheckboxItem
            key={item}
            checked={selected.includes(item)}
            onCheckedChange={() => onToggle(item)}
          >
            {item}
          </DropdownMenuCheckboxItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function SingleValueDropdown({
  label,
  value,
  options,
  onChange,
  widthClass = "min-w-36",
}: {
  label: string;
  value: string;
  options: Record<string, string>;
  onChange: (value: string) => void;
  widthClass?: string;
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className={`h-10 justify-between rounded-full border-slate-300 bg-white px-4 ${widthClass}`}
        >
          <span className="truncate">{options[value]}</span>
          <ChevronDown className="size-4 text-slate-400" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-48 rounded-2xl">
        <DropdownMenuLabel>{label}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuRadioGroup value={value} onValueChange={onChange}>
          {Object.entries(options).map(([key, optionLabel]) => (
            <DropdownMenuRadioItem key={key} value={key}>
              {optionLabel}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function DuplicateSwitch({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="inline-flex h-10 items-center gap-3 rounded-full border border-slate-300 bg-white px-4 text-sm text-slate-700 transition hover:bg-slate-50"
    >
      <span>重複を含める</span>
      <span
        className={
          checked
            ? "relative h-5 w-9 rounded-full bg-[#1a73e8] transition"
            : "relative h-5 w-9 rounded-full bg-slate-300 transition"
        }
      >
        <span
          className={
            checked
              ? "absolute top-0.5 left-[18px] size-4 rounded-full bg-white shadow-sm transition"
              : "absolute top-0.5 left-0.5 size-4 rounded-full bg-white shadow-sm transition"
          }
        />
      </span>
    </button>
  );
}

export function TechInsightDashboard({ bootstrap }: { bootstrap: DashboardBootstrap }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [, startTransition] = useTransition();
  const [notice, setNotice] = useState<string | null>(null);
  const [dialogArticle, setDialogArticle] = useState<ArticleSummary | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [queryDraft, setQueryDraft] = useState("");
  const [searchState, setSearchState] = useState<SearchRequest>({
    query: "",
    mode: "hybrid",
    filters: {
      category: [],
      author: [],
      publishedFrom: null,
      publishedTo: null,
    },
    sort: "relevance",
    includeDuplicates: true,
    page: 1,
    pageSize: 20,
  });

  const hasSearch = searchState.query.trim().length > 0;
  const effectiveSort = hasSearch
    ? searchState.sort
    : searchState.sort === "oldest"
      ? "oldest"
      : "newest";
  const isDefaultListState =
    !hasSearch &&
    searchState.page === 1 &&
    searchState.pageSize === 20 &&
    searchState.filters.category.length === 0 &&
    searchState.filters.author.length === 0 &&
    effectiveSort === "newest";

  const filtersQuery = useQuery({
    queryKey: ["filters"],
    queryFn: fetchFilters,
    initialData: bootstrap.filters,
  });

  const listQuery = useQuery({
    queryKey: [
      "articles",
      searchState.page,
      searchState.pageSize,
      searchState.filters.category,
      searchState.filters.author,
      effectiveSort,
    ],
    queryFn: () =>
      fetchArticles({
        page: searchState.page,
        pageSize: searchState.pageSize,
        category: searchState.filters.category,
        author: searchState.filters.author,
        sort:
          effectiveSort === "newest"
            ? "published_desc"
            : effectiveSort === "oldest"
              ? "published_asc"
              : "published_desc",
      }),
    initialData: isDefaultListState ? bootstrap.articles : undefined,
    placeholderData: (previousData) => previousData,
    enabled: !hasSearch,
  });

  const searchQuery = useQuery({
    queryKey: ["search", searchState],
    queryFn: () => searchArticles(searchState),
    enabled: hasSearch,
    placeholderData: (previousData) => previousData,
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: {
      articleId?: number;
      values: {
        title: string;
        content: string;
        author: string;
        category: string;
        published_at: string;
      };
    }) => {
      const requestBody = {
        ...payload.values,
        published_at: new Date(payload.values.published_at).toISOString(),
      };
      return payload.articleId
        ? updateArticle(payload.articleId, requestBody)
        : createArticle(requestBody);
    },
    onSuccess: () => {
      setDialogOpen(false);
      setDialogArticle(null);
      setNotice("保存しました");
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      queryClient.invalidateQueries({ queryKey: ["search"] });
      queryClient.invalidateQueries({ queryKey: ["filters"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (articleId: number) => deleteArticle(articleId),
    onSuccess: () => {
      setNotice("削除しました");
      queryClient.invalidateQueries({ queryKey: ["articles"] });
      queryClient.invalidateQueries({ queryKey: ["search"] });
      queryClient.invalidateQueries({ queryKey: ["filters"] });
    },
  });

  const rows = useMemo(() => {
    if (hasSearch) {
      return buildRowsFromSearch(
        searchQuery.data ?? {
          items: [],
          total: 0,
        },
      );
    }
    return (listQuery.data?.items ?? []).map(buildRowFromArticle);
  }, [hasSearch, listQuery.data, searchQuery.data]);

  const rowCount = hasSearch ? searchQuery.data?.total ?? 0 : listQuery.data?.total ?? 0;
  const hasDataError = Boolean(filtersQuery.error || listQuery.error || searchQuery.error);
  const totalPages = Math.max(1, Math.ceil(rowCount / searchState.pageSize));
  const isSearchFetching = hasSearch && searchQuery.isFetching;
  const isTableLoading = hasSearch
    ? isSearchFetching && rows.length === 0
    : listQuery.isFetching && rows.length === 0;
  const searchModeLabel = MODE_LABELS[searchState.mode];

  function toggleFilter(type: "category" | "author", value: string) {
    startTransition(() =>
      setSearchState((current) => {
        const values = current.filters[type];
        const nextValues = values.includes(value)
          ? values.filter((item) => item !== value)
          : [...values, value];
        return {
          ...current,
          filters: {
            ...current.filters,
            [type]: nextValues,
          },
          page: 1,
        };
      }),
    );
  }

  const summaryLabel = hasSearch ? "検索結果" : "記事";

  function applySearch(query: string) {
    const trimmed = query.trim();
    startTransition(() =>
      setSearchState((current) => ({
        ...current,
        query: trimmed,
        sort: trimmed ? "relevance" : "newest",
        page: 1,
      })),
    );
  }

  return (
    <div className="min-h-screen bg-[var(--background)] text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-2xl bg-[#e8f0fe] text-[#1a73e8]">
              <Search className="size-4" />
            </div>
            <div>
              <h1 className="text-[30px] leading-none font-semibold tracking-tight text-slate-950">
                TechInsight
              </h1>
              <p className="mt-1 text-sm text-slate-500">社内技術記事の検索と管理</p>
            </div>
          </div>
          <Button
            className="rounded-full bg-[#1a73e8] px-5 text-white hover:bg-[#1765cc]"
            onClick={() => {
              setDialogArticle(null);
              setDialogOpen(true);
            }}
          >
            <Plus className="mr-1 size-4" />
            記事を追加
          </Button>
        </div>
      </header>

      <main className="mx-auto flex max-w-[1440px] flex-col gap-5 px-6 py-6">
        <section className="rounded-[28px] border border-slate-200 bg-white px-5 py-5 shadow-sm">
          <div className="grid gap-4">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-slate-400" />
                <Input
                  value={queryDraft}
                  onChange={(event) => setQueryDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      applySearch(queryDraft);
                    }
                  }}
                  placeholder="記事を検索"
                  className="h-12 rounded-full border-slate-300 bg-[#f8fafd] pr-4 pl-11 text-[15px]"
                />
              </div>
              <div className="flex items-center gap-2">
                <Button
                  className="h-11 rounded-full bg-[#1a73e8] px-5 text-white hover:bg-[#1765cc]"
                  disabled={isSearchFetching}
                  onClick={() => applySearch(queryDraft)}
                >
                  {isSearchFetching ? <Loader2 className="mr-2 size-4 animate-spin" /> : null}
                  {isSearchFetching ? "検索中" : "検索"}
                </Button>
                <Button
                  variant="outline"
                  className="h-11 rounded-full border-slate-300 bg-white px-5"
                  onClick={() => {
                    setQueryDraft("");
                    applySearch("");
                  }}
                >
                  クリア
                </Button>
              </div>
            </div>

            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-center">
                <div className="inline-flex rounded-full bg-[#eef3fd] p-1">
                  {(Object.keys(MODE_LABELS) as SearchRequest["mode"][]).map((mode) => (
                    <button
                      key={mode}
                      type="button"
                      onClick={() =>
                        startTransition(() =>
                          setSearchState((current) => ({
                            ...current,
                            mode,
                            page: 1,
                          })),
                        )
                      }
                      className={
                        searchState.mode === mode
                          ? "inline-flex items-center gap-2 rounded-full bg-[#d2e3fc] px-4 py-2 text-sm font-medium text-[#174ea6]"
                          : "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm text-slate-600"
                      }
                    >
                      {isSearchFetching && searchState.mode === mode ? (
                        <Loader2 className="size-3.5 animate-spin" />
                      ) : null}
                      {MODE_LABELS[mode]}
                    </button>
                  ))}
                </div>

                <FilterDropdown
                  label="カテゴリ"
                  items={filtersQuery.data?.categories ?? []}
                  selected={searchState.filters.category}
                  onToggle={(value) => toggleFilter("category", value)}
                />
                <FilterDropdown
                  label="著者"
                  items={filtersQuery.data?.authors ?? []}
                  selected={searchState.filters.author}
                  onToggle={(value) => toggleFilter("author", value)}
                />
                <DuplicateSwitch
                  checked={searchState.includeDuplicates}
                  onChange={(checked) =>
                    startTransition(() =>
                      setSearchState((current) => ({
                        ...current,
                        includeDuplicates: checked,
                        page: 1,
                      })),
                    )
                  }
                />
              </div>

              <div className="flex flex-wrap items-center gap-2 text-sm text-slate-500">
                {searchState.filters.category.length > 0 ? (
                  <Badge className="rounded-md bg-[#eef3fd] text-[#355f9f] hover:bg-[#e4ecff]">
                    カテゴリ {searchState.filters.category.length}
                  </Badge>
                ) : null}
                {searchState.filters.author.length > 0 ? (
                  <Badge className="rounded-md bg-[#eef3fd] text-[#355f9f] hover:bg-[#e4ecff]">
                    著者 {searchState.filters.author.length}
                  </Badge>
                ) : null}
              </div>
            </div>

            {hasDataError ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                データを読み込めません。バックエンド接続を確認してください。
              </div>
            ) : null}

            {isSearchFetching ? (
              <div
                role="status"
                aria-live="polite"
                className="flex items-center gap-2 rounded-2xl border border-[#d2e3fc] bg-[#f8fafd] px-4 py-3 text-sm text-[#174ea6]"
              >
                <Loader2 className="size-4 animate-spin" />
                <span>{searchModeLabel}で検索しています。</span>
              </div>
            ) : null}
          </div>
        </section>

        <section className="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">記事一覧</h2>
              <p className="mt-1 text-sm text-slate-500">
                一覧から詳細確認、編集、削除まで行えます。
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-slate-500">
                {summaryLabel} {rowCount.toLocaleString()} 件
              </span>
              <SingleValueDropdown
                label={hasSearch ? "並び順" : "公開順"}
                value={effectiveSort}
                options={hasSearch ? SORT_LABELS : LIST_SORT_LABELS}
                widthClass="w-[160px]"
                onChange={(value) =>
                  startTransition(() =>
                    setSearchState((current) => ({
                      ...current,
                      sort: value as SearchRequest["sort"],
                      page: 1,
                    })),
                  )
                }
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <Table className="min-w-[1080px]">
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[60%] px-5 text-xs font-semibold text-slate-500">
                    タイトル
                  </TableHead>
                  <TableHead className="w-[10%] text-xs font-semibold text-slate-500">
                    カテゴリ
                  </TableHead>
                  <TableHead className="w-[10%] text-xs font-semibold text-slate-500">著者</TableHead>
                  <TableHead className="w-[10%] text-xs font-semibold text-slate-500">
                    公開日
                  </TableHead>
                  {hasSearch ? (
                    <TableHead className="w-[6%] text-xs font-semibold text-slate-500">
                      関連度
                    </TableHead>
                  ) : null}
                  <TableHead className="w-[4%] pr-5 text-right text-xs font-semibold text-slate-500">
                    操作
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isTableLoading ? (
                  <TableRow>
                    <TableCell
                      colSpan={hasSearch ? 6 : 5}
                      className="px-5 py-16 text-center text-sm text-slate-500"
                    >
                      <div
                        role="status"
                        aria-live="polite"
                        className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-slate-600"
                      >
                        <Loader2 className="size-4 animate-spin text-[#1a73e8]" />
                        <span>
                          {hasSearch
                            ? `${searchModeLabel}で検索しています`
                            : "記事を読み込んでいます"}
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : rows.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={hasSearch ? 6 : 5}
                      className="px-5 py-16 text-center text-sm text-slate-500"
                    >
                      該当する記事がありません。
                    </TableCell>
                  </TableRow>
                ) : (
                  rows.map((row) => (
                    <TableRow
                      key={row.id}
                      className="cursor-pointer hover:bg-slate-50"
                      onClick={() => router.push(buildArticlePath(row.id, row.title))}
                      onMouseEnter={() => router.prefetch(buildArticlePath(row.id, row.title))}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          router.push(buildArticlePath(row.id, row.title));
                        }
                      }}
                      tabIndex={0}
                    >
                      <TableCell className="px-5 py-3">
                        <div className="flex min-w-0 flex-col gap-1">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <div className="truncate text-[15px] font-medium text-slate-900">
                                {row.title}
                              </div>
                            </TooltipTrigger>
                            <TooltipContent>{row.title}</TooltipContent>
                          </Tooltip>
                          {row.source === "search" && row.matchedBy.length > 0 ? (
                            <div className="flex flex-wrap gap-1.5">
                              {row.matchedBy.slice(0, 3).map((item) => (
                                <Badge
                                  key={item}
                                  className="rounded-md bg-[#eef3fd] text-[11px] text-[#355f9f] hover:bg-[#e4ecff]"
                                >
                                  {item}
                                </Badge>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-slate-600">{row.category}</TableCell>
                      <TableCell className="text-sm text-slate-600">{row.author}</TableCell>
                      <TableCell className="text-sm text-slate-600">
                        {formatDate(row.publishedAt)}
                      </TableCell>
                      {hasSearch ? (
                        <TableCell className="text-sm text-slate-600">
                          {row.score ? row.score.toFixed(3) : "-"}
                        </TableCell>
                      ) : null}
                      <TableCell className="pr-4">
                        <div className="flex items-center justify-end gap-1">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                className="rounded-full text-slate-500 hover:text-slate-900"
                                onClick={async (event) => {
                                  event.stopPropagation();
                                  const raw =
                                    row.raw ??
                                    bootstrap.articles.items.find((item) => item.id === row.id) ??
                                    (await queryClient.fetchQuery({
                                      queryKey: ["article", row.id],
                                      queryFn: () => fetchArticleDetail(row.id),
                                    }));
                                  if (!raw) return;
                                  setDialogArticle({
                                    id: raw.id,
                                    title: raw.title,
                                    content: raw.content,
                                    author: raw.author,
                                    category: raw.category,
                                    published_at: raw.published_at,
                                    created_at: raw.created_at,
                                    updated_at: raw.updated_at,
                                  });
                                  setDialogOpen(true);
                                }}
                              >
                                <Pencil className="size-4" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>編集</TooltipContent>
                          </Tooltip>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                className="rounded-full text-slate-500 hover:text-red-600"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  if (window.confirm("この記事を削除しますか？")) {
                                    deleteMutation.mutate(row.id);
                                  }
                                }}
                              >
                                <Trash2 className="size-4" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>削除</TooltipContent>
                          </Tooltip>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          <Separator />
          <div className="flex flex-col gap-3 px-5 py-4 text-sm text-slate-500 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <span>1ページあたり</span>
              <SingleValueDropdown
                label="件数"
                value={String(searchState.pageSize) as "10" | "20" | "50"}
                options={{ "10": "10", "20": "20", "50": "50" }}
                widthClass="w-[96px]"
                onChange={(value) =>
                  startTransition(() =>
                    setSearchState((current) => ({
                      ...current,
                      pageSize: Number(value),
                      page: 1,
                    })),
                  )
                }
              />
            </div>

            <div className="flex items-center gap-4">
              <span>
                {Math.min((searchState.page - 1) * searchState.pageSize + 1, rowCount)}-
                {Math.min(searchState.page * searchState.pageSize, rowCount)} / {rowCount.toLocaleString()}
              </span>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="rounded-full"
                  disabled={searchState.page <= 1}
                  onClick={() =>
                    startTransition(() =>
                      setSearchState((current) => ({
                        ...current,
                        page: Math.max(1, current.page - 1),
                      })),
                    )
                  }
                >
                  <ChevronLeft className="size-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="rounded-full"
                  disabled={searchState.page >= totalPages}
                  onClick={() =>
                    startTransition(() =>
                      setSearchState((current) => ({
                        ...current,
                        page: Math.min(totalPages, current.page + 1),
                      })),
                    )
                  }
                >
                  <ChevronRight className="size-4" />
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <ArticleFormDialog
        article={dialogArticle}
        open={dialogOpen}
        submitting={saveMutation.isPending}
        onClose={() => {
          setDialogOpen(false);
          setDialogArticle(null);
        }}
        onSubmit={(values) =>
          saveMutation.mutate({
            articleId: dialogArticle?.id,
            values,
          })
        }
      />

      {notice ? (
        <div className="fixed right-5 bottom-5 z-30">
          <div className="rounded-full bg-slate-900 px-4 py-2 text-sm text-white shadow-lg">
            {notice}
          </div>
        </div>
      ) : null}
    </div>
  );
}
