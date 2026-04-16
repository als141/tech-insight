import Link from "next/link";

import { ArrowLeft, ArrowUpRight, CalendarDays, FolderKanban, UserRound } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import { buildArticlePath } from "../lib/article-path";
import type { ArticleDetail } from "../lib/types";

function formatDateTime(value: string) {
  return value.replace("T", " ").replace("Z", "").slice(0, 16);
}

function ArticleLinkList({
  title,
  items,
}: {
  title: string;
  items: { id: number; title: string; author: string; category: string; published_at: string }[];
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-950">{title}</h2>
      </div>
      <div className="divide-y divide-slate-200">
        {items.map((item) => (
          <Link
            key={item.id}
            href={buildArticlePath(item.id, item.title)}
            className="flex items-start justify-between gap-4 px-5 py-4 transition hover:bg-slate-50"
          >
            <div className="min-w-0">
              <div className="truncate text-sm font-medium text-slate-900">{item.title}</div>
              <div className="mt-1 text-xs text-slate-500">
                {item.author} / {item.category} / {formatDateTime(item.published_at)}
              </div>
            </div>
            <ArrowUpRight className="mt-0.5 size-4 shrink-0 text-slate-400" />
          </Link>
        ))}
      </div>
    </section>
  );
}

export function ArticleDetailPage({ article }: { article: ArticleDetail }) {
  return (
    <div className="min-h-screen bg-[var(--background)] text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="inline-flex h-10 items-center gap-2 rounded-full border border-slate-200 px-4 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              <ArrowLeft className="size-4" />
              記事一覧
            </Link>
            <Link href="/" className="text-[28px] leading-none font-semibold tracking-tight text-slate-950">
              TechInsight
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-[1200px] gap-6 px-6 py-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <div className="border-b border-slate-200 px-6 py-6">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="rounded-md bg-[#eef3fd] text-[#355f9f] hover:bg-[#eef3fd]">
                {article.category}
              </Badge>
              <span className="inline-flex items-center gap-1 text-sm text-slate-500">
                <UserRound className="size-4" />
                {article.author}
              </span>
              <span className="inline-flex items-center gap-1 text-sm text-slate-500">
                <CalendarDays className="size-4" />
                {formatDateTime(article.published_at)}
              </span>
            </div>
            <h1 className="mt-4 text-[30px] leading-10 font-semibold tracking-tight text-slate-950">
              {article.title}
            </h1>
          </div>

          <div className="px-6 py-6">
            <div className="whitespace-pre-wrap text-[15px] leading-8 text-slate-800">
              {article.content}
            </div>
          </div>
        </article>

        <aside className="grid gap-5 self-start xl:sticky xl:top-[92px]">
          <section className="rounded-2xl border border-slate-200 bg-white px-5 py-5">
            <h2 className="text-sm font-semibold text-slate-950">記事情報</h2>
            <Separator className="my-4" />
            <div className="grid gap-4 text-sm text-slate-600">
              <div className="grid gap-1">
                <span className="text-xs font-medium tracking-wide text-slate-400 uppercase">
                  Category
                </span>
                <span className="inline-flex items-center gap-2 text-slate-800">
                  <FolderKanban className="size-4 text-slate-400" />
                  {article.category}
                </span>
              </div>
              <div className="grid gap-1">
                <span className="text-xs font-medium tracking-wide text-slate-400 uppercase">
                  Author
                </span>
                <span className="text-slate-800">{article.author}</span>
              </div>
              <div className="grid gap-1">
                <span className="text-xs font-medium tracking-wide text-slate-400 uppercase">
                  Published
                </span>
                <span className="text-slate-800">{formatDateTime(article.published_at)}</span>
              </div>
            </div>
          </section>

          <ArticleLinkList
            title={`同内容の別版 ${article.duplicate_count} 件`}
            items={article.variants}
          />
          <ArticleLinkList title="関連候補" items={article.related_articles} />
        </aside>
      </main>
    </div>
  );
}
