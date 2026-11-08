// TD2 Loot Advisor — Xbox Companion.
// meta/meta_builds.json'daki popüler build özetlerini temsil eder (ayrıntılı
// attribute/talent ağırlıkları bu ilk sürümde gösterilmiyor — kapsam
// bilinçli olarak basit tutuldu, bkz. xbox-companion/README.md).
using System.Collections.Generic;
using Windows.Data.Json;

namespace XboxCompanion.Models
{
    public sealed class MetaBuild
    {
        public string Id { get; private set; }
        public string Name { get; private set; }
        public string Mode { get; private set; }
        public string Role { get; private set; }
        public int SetBonus { get; private set; }
        public int Popularity { get; private set; }
        public IReadOnlyList<string> SetsOrBrands { get; private set; }
        public IReadOnlyList<string> Items { get; private set; }

        /// Yalnız "tr" ve "en" mevcut (bkz. meta_builds.json) — seçili dil
        /// bunların dışındaysa İngilizceye düşülür.
        public IReadOnlyDictionary<string, string> Summary { get; private set; }

        public string SummaryFor(string langCode)
        {
            if (Summary == null) return null;
            if (Summary.TryGetValue(langCode, out var value)) return value;
            if (Summary.TryGetValue("en", out var fallback)) return fallback;
            return null;
        }

        public static MetaBuild FromJson(JsonObject obj)
        {
            return new MetaBuild
            {
                Id = obj.GetNamedString("id", ""),
                Name = obj.GetNamedString("name", ""),
                Mode = obj.GetNamedString("mode", ""),
                Role = obj.GetNamedString("role", ""),
                SetBonus = (int)obj.GetNamedNumber("set_bonus", 0),
                Popularity = (int)obj.GetNamedNumber("popularity", 0),
                SetsOrBrands = ReadStringArray(obj, "sets_or_brands"),
                Items = ReadStringArray(obj, "items"),
                Summary = ReadLangDict(obj, "summary"),
            };
        }

        static List<string> ReadStringArray(JsonObject obj, string key)
        {
            var result = new List<string>();
            if (!obj.ContainsKey(key) || obj[key].ValueType != JsonValueType.Array) return result;
            foreach (var item in obj[key].GetArray())
            {
                if (item.ValueType == JsonValueType.String) result.Add(item.GetString());
            }
            return result;
        }

        static Dictionary<string, string> ReadLangDict(JsonObject obj, string key)
        {
            var result = new Dictionary<string, string>();
            if (!obj.ContainsKey(key) || obj[key].ValueType != JsonValueType.Object) return result;
            foreach (var pair in obj[key].GetObject())
            {
                if (pair.Value.ValueType == JsonValueType.String) result[pair.Key] = pair.Value.GetString();
            }
            return result;
        }
    }
}
