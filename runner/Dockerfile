# Pinned toolchains: every localcode user judges against exactly these versions.
FROM python:3.12.12-slim-trixie

RUN apt-get update \
 && apt-get install -y --no-install-recommends g++ nlohmann-json3-dev curl unzip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY --from=eclipse-temurin:21.0.5_11-jdk /opt/java/openjdk /opt/java

ARG KOTLIN_VERSION=2.0.21
RUN curl -fsSL -o /tmp/k.zip https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip \
 && unzip -q /tmp/k.zip -d /opt && rm /tmp/k.zip

RUN mkdir -p /opt/lib \
 && curl -fsSL -o /opt/lib/gson.jar https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar

ENV JAVA_HOME=/opt/java PATH=/opt/java/bin:/opt/kotlinc/bin:$PATH

RUN pip install --no-cache-dir pytest==8.3.4 \
 && useradd -u 10001 -M -s /usr/sbin/nologin sandbox

WORKDIR /srv
COPY . /srv
RUN if [ -f harness/jvm/Driver.java ]; then \
      mkdir -p /tmp/drv && javac -cp /opt/lib/gson.jar -d /tmp/drv harness/jvm/Driver.java \
      && jar cf /opt/lib/driver.jar -C /tmp/drv . && rm -rf /tmp/drv; fi

EXPOSE 8080
CMD ["python", "-u", "server.py"]
