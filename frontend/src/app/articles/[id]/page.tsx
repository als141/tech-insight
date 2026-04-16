import { notFound, redirect } from "next/navigation";

import { getArticleDetailById } from "../../../lib/api";
import { buildArticlePath } from "../../../lib/article-path";

export const dynamic = "force-dynamic";

export default async function ArticleIdRedirectPage({
  params,
}: {
  params: Promise<{ id: string }>;
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

  redirect(buildArticlePath(article.id, article.title));
}
