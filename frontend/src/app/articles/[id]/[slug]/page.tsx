import { notFound } from "next/navigation";

import { ArticleDetailPage } from "../../../../components/article-detail-page";
import { getArticleDetailById } from "../../../../lib/api";

export const dynamic = "force-dynamic";

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ id: string; slug: string }>;
}) {
  const { id } = await params;
  const articleId = Number(id);

  if (!Number.isInteger(articleId) || articleId <= 0) {
    notFound();
  }

  let article;
  try {
    article = await getArticleDetailById(articleId);
  } catch {
    notFound();
  }

  return <ArticleDetailPage article={article} />;
}
