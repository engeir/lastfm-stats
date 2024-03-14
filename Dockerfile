# Stage 1: init
FROM python:3.11

# Pass `--build-arg API_URL=http://app.example.com:8000` during build
# ARG API_URL
# ARG API_URL=http://music.eirik.re:8000

# Copy local context to `/lastfm` inside container (see .dockerignore)
WORKDIR /lastfm
COPY . .

# Create virtualenv which will be copied into final container
# ENV VIRTUAL_ENV=/.venv
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# RUN python3.11 -m venv $VIRTUAL_ENV

# Install app requirements and reflex inside virtualenv
RUN pip install -r requirements.txt

# Deploy templates and prepare app
RUN reflex init

# Export static copy of frontend to /lastfm/.web/_static
RUN reflex export --frontend-only --no-zip

# Copy static files out of /lastfm to save space in backend image
# RUN mv .web/_static /tmp/_static
# RUN rm -rf .web && mkdir .web
# RUN mv /tmp/_static .web/_static

# Stage 2: copy artifacts into slim image 
# FROM python:3.11-slim
# ARG API_URL
# WORKDIR /lastfm
# RUN adduser --disabled-password --home /lastfm me
# COPY --chown=me --from=init /lastfm /lastfm
# USER me
# ENV PATH="/lastfm/.venv/bin:/.venv/bin:$PATH" API_URL=$API_URL

# CMD reflex db migrate && reflex run --env prod --backend-only

# Needed until Reflex properly passes SIGTERM on backend.
STOPSIGNAL SIGKILL

# Always apply migrations before starting the backend.
CMD [ -d alembic ] && reflex db migrate; reflex run --env prod
