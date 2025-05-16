FROM denoland/deno:alpine-2.3.1

WORKDIR /app
EXPOSE 8007
COPY ./app .

RUN deno install && \
    deno run build && \
    deno run -A jsr:@std/http/file-server dist --port 8007
