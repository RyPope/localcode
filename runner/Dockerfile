# Pinned toolchains: every localcode user judges against exactly these versions.
FROM python:3.14.10-slim-trixie AS runtime

# Clang comes from LLVM's own apt repository (Debian's is a few majors behind). Its signing key is
# pinned by checksum; the fingerprint is 6084F3CF814B57C1CF12EFD515CF4D18AF4F7421.
ARG CLANG_MAJOR=23
ARG LLVM_KEY_SHA256=8b2a587ffd672c4687e7581dad4b2f6c1bb2ad6b480cd9771ba2ff48e0b8c75d
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -fsSL -o /etc/apt/keyrings/llvm.asc https://apt.llvm.org/llvm-snapshot.gpg.key \
 && echo "${LLVM_KEY_SHA256}  /etc/apt/keyrings/llvm.asc" | sha256sum -c - \
 && echo "deb [signed-by=/etc/apt/keyrings/llvm.asc] https://apt.llvm.org/trixie/ llvm-toolchain-trixie-${CLANG_MAJOR} main" \
      > /etc/apt/sources.list.d/llvm.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends clang-${CLANG_MAJOR} g++ nlohmann-json3-dev unzip \
 && ln -s /usr/bin/clang++-${CLANG_MAJOR} /usr/local/bin/clang++ \
 && rm -rf /var/lib/apt/lists/*

COPY --from=eclipse-temurin:25.0.5_8-jdk /opt/java/openjdk /opt/java

# Downloads are verified against pinned SHA-256 checksums (Kotlin's matches JetBrains' published
# .sha256; Gson's was computed from the jar matching Maven Central's published SHA-1).
ARG KOTLIN_VERSION=2.4.21
ARG KOTLIN_SHA256=7cc140e76daf416a0424a5557f99afd7ca89ebd463ea1101261e3e01c33e75cd
RUN curl -fsSL -o /tmp/k.zip https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip \
 && echo "${KOTLIN_SHA256}  /tmp/k.zip" | sha256sum -c - \
 && unzip -q /tmp/k.zip -d /opt && rm /tmp/k.zip

ARG GSON_VERSION=2.15.0
ARG GSON_SHA256=96d3dd843dc2911de01cdabcd50064cb9e860353102a0a78c96fd833d396fc7d
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

# C++ is compiled with Clang against libstdc++ (installed with g++).
# Precompiled prelude; flags must match CPP_FLAGS in languages.py.
RUN mkdir -p /opt/lc && cp harness/cpp/lc.hpp harness/cpp/lc_io.cpp /opt/lc/ \
 && clang++ -std=c++23 -O2 -w -x c++-header /opt/lc/lc.hpp -o /opt/lc/lc.hpp.pch \
 && clang++ -std=c++23 -O2 -w -I /opt/lc -include-pch /opt/lc/lc.hpp.pch -c /opt/lc/lc_io.cpp -o /opt/lc/lc_io.o

COPY server.py execute.py sandbox.py languages.py ./

EXPOSE 8080
CMD ["python", "-u", "server.py"]

# Test image: the runtime plus pytest and the test suite (never shipped).
FROM runtime AS test
RUN pip install --no-cache-dir pytest==9.2.0
COPY pytest.ini ./
COPY tests/ tests/
CMD ["pytest", "-q", "tests/"]
