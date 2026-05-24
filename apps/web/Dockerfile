FROM node:24-alpine

WORKDIR /workspace

RUN corepack enable
RUN chown node:node /workspace

COPY --chown=node:node package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --chown=node:node apps/web/package.json apps/web/package.json
USER node

RUN pnpm install --filter @dealmoa/web --frozen-lockfile

COPY --chown=node:node apps/web apps/web

WORKDIR /workspace/apps/web

CMD ["pnpm", "dev", "--hostname", "0.0.0.0", "--port", "3000"]
