# Hetu Protocol Buffers

This directory contains the Protocol Buffers definitions for the Hetu project.

To generate the Python code from these definitions, you need to have `buf` installed.

You can install `buf` by following the instructions at https://buf.build/docs/installation.

After installing `buf`, you can generate the Python code by running the following command:

```bash
cd hetu/proto
buf generate --include-imports
```