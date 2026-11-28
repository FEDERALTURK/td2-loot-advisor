import worker from "./worker.js";
import { requireHashSalt } from "./security.js";

const assert = (condition, message) => {
  if (!condition) throw new Error(message);
  console.log("OK", message);
};

assert(requireHashSalt({ HASH_SALT: "a-random-test-only-salt-with-at-least-32-chars" })
  === "a-random-test-only-salt-with-at-least-32-chars", "configured hash salt accepted");
for (const env of [{}, { HASH_SALT: "" }, { HASH_SALT: "dev-salt" }]) {
  let rejected = false;
  try { requireHashSalt(env); } catch { rejected = true; }
  assert(rejected, "missing or weak hash salt rejected");
}

const response = await worker.fetch(
  new Request("https://example.test/v1/health"),
  { DB: { prepare() { throw new Error("must not reach database"); } } },
  {}
);
assert(response.status === 503, "Worker fails closed before handling requests without the secret");

const oversized = new Request("https://example.test/v1/health", {
  method: "POST",
  body: new ReadableStream({
    start(controller) {
      controller.enqueue(new Uint8Array(256 * 1024));
      controller.enqueue(new Uint8Array(1));
      controller.close();
    },
  }),
  duplex: "half",
});
const bounded = await worker.fetch(oversized, { HASH_SALT: "test-only-hash-salt-with-at-least-32-characters" }, {});
assert(bounded.status === 413, "streaming request bodies above the cap are rejected without Content-Length");
