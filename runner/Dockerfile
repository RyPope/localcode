# Pinned toolchains: every localcode user judges against exactly these versions.
FROM python:3.12.15-slim-trixie AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends clang g++ nlohmann-json3-dev curl unzip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY --from=eclipse-temurin:21.0.5_11-jdk /opt/java/openjdk /opt/java

# Downloads are verified against pinned SHA-256 checksums (Kotlin's matches JetBrains' published
# .sha256; Gson's was computed from the jar matching Maven Central's published SHA-1).
ARG KOTLIN_VERSION=2.0.21
ARG KOTLIN_SHA256=0352c0a45bd22f80f6b26e485cd04da8047baa5de54865281fb9f89a4a7bcf2a
RUN curl -fsSL -o /tmp/k.zip https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip \
 && echo "${KOTLIN_SHA256}  /tmp/k.zip" | sha256sum -c - \
 && unzip -q /tmp/k.zip -d /opt && rm /tmp/k.zip

ARG GSON_VERSION=2.11.0
ARG GSON_SHA256=57928d6e5a6edeb2abd3770a8f95ba44dce45f3b23b7a9dc2b309c581552a78b
RUN mkdir -p /opt/lib \
 && curl -fsSL -o /opt/lib/gson.jar https://repo1.maven.org/maven2/com/google/code/gson/gson/${GSON_VERSION}/gson-${GSON_VERSION}.jar \
 && echo "${GSON_SHA256}  /opt/lib/gson.jar" | sha256sum -c -

ENV JAVA_HOME=/opt/java PATH=/opt/java/bin:/opt/kotlinc/bin:$PATH
RUN useradd -u 10001 -M -s /usr/sbin/nologin sandbox

WORKDIR /srv
COPY harness/ harness/

RUN mkdir -p /tmp/drv \
 && javac -cp /opt/lib/gson.jar -d /tmp/drv harness/jvm/Driver.java harness/jvm/javafx/util/Pair.java \
 && jar cf /opt/lib/driver.jar -C /tmp/drv . && rm -rf /tmp/drv

# C++ is compiled with Clang (as LeetCode does) against libstdc++ (installed with g++).
# Precompiled prelude; flags must match CPP_FLAGS in languages.py.
RUN mkdir -p /opt/lc && cp harness/cpp/lc.hpp harness/cpp/lc_io.cpp /opt/lc/ \
 && clang++ -std=c++23 -O2 -w -x c++-header /opt/lc/lc.hpp -o /opt/lc/lc.hpp.pch \
 && clang++ -std=c++23 -O2 -w -I /opt/lc -include-pch /opt/lc/lc.hpp.pch -c /opt/lc/lc_io.cpp -o /opt/lc/lc_io.o

COPY server.py execute.py sandbox.py languages.py ./

EXPOSE 8080
CMD ["python", "-u", "server.py"]

# Test image: the runtime plus pytest and the test suite (never shipped).
FROM runtime AS test
RUN pip install --no-cache-dir pytest==8.3.4
COPY pytest.ini ./
COPY tests/ tests/
CMD ["pytest", "-q", "tests/"]
