"use client";

import { useEffect } from "react";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import type { ArticleSummary } from "../lib/types";

const schema = z.object({
  title: z.string().min(3),
  content: z.string().min(20),
  author: z.string().min(2),
  category: z.string().min(2),
  published_at: z.string().min(1),
});

type FormValues = z.infer<typeof schema>;

const CATEGORIES = ["AI/ML", "Backend", "DevOps", "Frontend"];

function toDateTimeLocal(value?: string) {
  if (!value) {
    return "";
  }
  return new Date(value).toISOString().slice(0, 16);
}

export function ArticleFormDialog({
  article,
  open,
  submitting,
  onClose,
  onSubmit,
}: {
  article: ArticleSummary | null;
  open: boolean;
  submitting: boolean;
  onClose: () => void;
  onSubmit: (values: FormValues) => void;
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: "",
      content: "",
      author: "",
      category: "Backend",
      published_at: "",
    },
  });

  useEffect(() => {
    reset({
      title: article?.title ?? "",
      content: article?.content ?? "",
      author: article?.author ?? "",
      category: article?.category ?? "Backend",
      published_at: toDateTimeLocal(article?.published_at),
    });
  }, [article, reset]);

  return (
    <Dialog open={open} onOpenChange={(next) => (!next ? onClose() : null)}>
      <DialogContent className="max-h-[calc(100vh-2rem)] max-w-[calc(100vw-2rem)] overflow-hidden rounded-[28px] border-slate-200 p-0 sm:max-w-3xl">
        <form className="flex max-h-[calc(100vh-2rem)] flex-col" onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader className="border-b border-slate-200 px-7 py-5 pr-16">
            <DialogTitle className="text-xl font-semibold text-slate-900">
              {article ? "記事を編集" : "記事を追加"}
            </DialogTitle>
          </DialogHeader>

          <div className="grid flex-1 gap-5 overflow-y-auto px-7 py-6">
            <div className="grid gap-2">
              <Label htmlFor="title">タイトル</Label>
              <Input id="title" className="h-11 rounded-xl" {...register("title")} />
              {errors.title ? (
                <p className="text-sm text-red-600">{errors.title.message}</p>
              ) : null}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="content">本文</Label>
              <Textarea
                id="content"
                className="min-h-56 rounded-2xl resize-y"
                {...register("content")}
              />
              {errors.content ? (
                <p className="text-sm text-red-600">{errors.content.message}</p>
              ) : null}
            </div>

            <div className="grid gap-5 md:grid-cols-3">
              <div className="grid gap-2">
                <Label htmlFor="author">著者</Label>
                <Input id="author" className="h-11 rounded-xl" {...register("author")} />
                {errors.author ? (
                  <p className="text-sm text-red-600">{errors.author.message}</p>
                ) : null}
              </div>

              <div className="grid gap-2">
                <Label>カテゴリ</Label>
                <select
                  className="h-11 rounded-xl border border-slate-300 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-[#1a73e8]/20"
                  {...register("category")}
                >
                  {CATEGORIES.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
                {errors.category ? (
                  <p className="text-sm text-red-600">{errors.category.message}</p>
                ) : null}
              </div>

              <div className="grid gap-2">
                <Label htmlFor="published_at">公開日時</Label>
                <Input
                  id="published_at"
                  type="datetime-local"
                  className="h-11 rounded-xl"
                  {...register("published_at")}
                />
                {errors.published_at ? (
                  <p className="text-sm text-red-600">{errors.published_at.message}</p>
                ) : null}
              </div>
            </div>
          </div>

          <DialogFooter className="mx-0 mb-0 rounded-none rounded-b-[28px] border-t border-slate-200 bg-slate-50 px-7 py-4">
            <Button type="button" variant="outline" className="rounded-full" onClick={onClose}>
              キャンセル
            </Button>
            <Button type="submit" className="rounded-full" disabled={submitting}>
              {article ? "更新する" : "作成する"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
