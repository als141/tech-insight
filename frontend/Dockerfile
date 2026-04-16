FROM oven/bun:1.3.9

WORKDIR /app/frontend

COPY frontend/package.json frontend/bun.lock /app/frontend/
RUN bun install --frozen-lockfile

COPY frontend /app/frontend

RUN bun run build

EXPOSE 3000

CMD ["bun", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
