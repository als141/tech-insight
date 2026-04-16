export function slugifyArticleTitle(title: string) {
  const slug = title
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");

  return slug || "article";
}

export function buildArticlePath(articleId: number, title: string) {
  return `/articles/${articleId}/${slugifyArticleTitle(title)}`;
}

