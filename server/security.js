export function requireHashSalt(env) {
  const value = env?.HASH_SALT;
  if (typeof value !== "string" || value.trim().length < 32)
    throw new Error("HASH_SALT must be configured with at least 32 characters");
  return value;
}
