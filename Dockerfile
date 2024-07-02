# Stage 1 - setup env variables
FROM python:3-alpine AS basebuild

LABEL org.opencontainers.image.authors="Michael Wan"

#Note for directories
#/opt
#/opt/ytdlp

# define app directory
ARG APP_DIR
ENV APP_DIR=${APP_DIR:-/opt/ytdlp}

# define tools directory
ARG TOOLS_DIR
ENV TOOLS_DIR=${TOOLS_DIR:-/opt}

# define media output directory
ARG MEDIA_DIR
ENV MEDIA_DIR=${MEDIA_DIR:-/media}

# define timezone
#ENV TZ=Asia/Hong_Kong

# define OS user to startup the server
ARG APP_USER=ytdlp
ARG APP_USER_GROUP=ytdlp

# create app user
RUN addgroup -S ${APP_USER_GROUP} && adduser -S ${APP_USER} -G ${APP_USER_GROUP}

################################################################################

# Stage 2 - setup app related files
FROM basebuild AS appbuild

# install git, ssh-client for app building
RUN apk add --no-cache git

# init directories it if not exist
RUN mkdir -p ${APP_DIR}

# change working directory
WORKDIR ${TOOLS_DIR}

# download app repos
RUN git clone https://github.com/micwan88/yt-dlp-wrapper.git ytdlp

################################################################################

# Stage 3 - final output
FROM basebuild AS finalbuild

# declare app folder is an external volume
VOLUME ${APP_DIR}

# install timezonedata, git, ffmpeg (use for mixing audio)
RUN apk add --no-cache tzdata git ffmpeg

# copying app files from last build
COPY --from=appbuild --chown=${APP_USER}:${APP_USER_GROUP} --chmod=750 ${APP_DIR} ${APP_DIR}

# switch to app user
USER ${APP_USER}:${APP_USER_GROUP}

# change working directory
WORKDIR ${APP_DIR}

# upgrade pip
RUN pip install --upgrade pip

# install python packages
RUN pip install -r requirements.txt

# define image entrypoint
ENTRYPOINT ["./run.sh"]
