FROM denoland/deno:alpine-2.3.1

WORKDIR /app
EXPOSE 8007
COPY ./app .

RUN deno install && \
    deno run build

CMD ["deno", "run", "-A", "./dist/server/entry.mjs"]
