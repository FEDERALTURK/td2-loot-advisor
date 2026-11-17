// TD2 Loot Advisor — Xbox Companion.
// meta/tasks_feed.json'daki her görevi temsil eder (günlük/haftalı manhunt
// ve journey görevleri — bkz. Thedivision2program/tasks_live.py).
// WinRT'nin yerleşik Windows.Data.Json ayrıştırıcısı kullanılıyor; ek bir
// NuGet bağımlılığı (System.Text.Json vb.) eklemek bu ilk sürümde riski
// artırır (bkz. XboxCompanion.csproj üstündeki not).
using System.Collections.Generic;
using Windows.Data.Json;

namespace XboxCompanion.Models
{
    public sealed class TaskItem
    {
        public string Id { get; private set; }
        public string Category { get; private set; }
        public string WikiId { get; private set; }
        public string SourceUrl { get; private set; }

        /// Dil kodu (en, tr, de, ...) → görev metni.
        public IReadOnlyDictionary<string, string> Text { get; private set; }

        /// Dil kodu → "nasıl yapılır" açıklaması (bazı görevlerde boş olabilir).
        public IReadOnlyDictionary<string, string> How { get; private set; }

        public string TextFor(string langCode) => Lookup(Text, langCode);
        public string HowFor(string langCode) => Lookup(How, langCode);

        static string Lookup(IReadOnlyDictionary<string, string> dict, string langCode)
        {
            if (dict == null) return null;
            if (dict.TryGetValue(langCode, out var value)) return value;
            if (dict.TryGetValue("en", out var fallback)) return fallback;
            return null;
        }

        public static TaskItem FromJson(JsonObject obj)
        {
            return new TaskItem
            {
                Id = obj.GetNamedString("id", ""),
                Category = obj.GetNamedString("cat", ""),
                WikiId = obj.GetNamedString("wiki_id", ""),
                SourceUrl = obj.ContainsKey("source") && obj["source"].ValueType == JsonValueType.Object
                    ? obj["source"].GetObject().GetNamedString("url", "")
                    : "",
                Text = ReadLangDict(obj, "text"),
                How = ReadLangDict(obj, "how"),
            };
        }

        static Dictionary<string, string> ReadLangDict(JsonObject obj, string key)
        {
            var result = new Dictionary<string, string>();
            if (!obj.ContainsKey(key) || obj[key].ValueType != JsonValueType.Object) return result;
            var langObj = obj[key].GetObject();
            foreach (var pair in langObj)
            {
                if (pair.Value.ValueType == JsonValueType.String)
                {
                    result[pair.Key] = pair.Value.GetString();
                }
            }
            return result;
        }
    }
}
