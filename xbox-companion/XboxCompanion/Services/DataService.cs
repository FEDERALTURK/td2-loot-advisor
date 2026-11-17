// TD2 Loot Advisor — Xbox Companion.
// Pakete gömülü JSON'ları (Assets/data/) okuyup Models/ sınıflarına çevirir.
// Bu ilk sürümde veri TAMAMEN STATİK (uygulama güncellemesiyle yenilenir) —
// canlı senkronizasyon (masaüstü/mobil companion'daki meta_sync.py/
// mobile_pairing benzeri) kapsam dışı, bkz. xbox-companion/README.md.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Windows.Data.Json;
using Windows.Storage;
using XboxCompanion.Models;

namespace XboxCompanion.Services
{
    public sealed class DataService
    {
        public IReadOnlyList<TaskItem> Tasks { get; private set; } = new List<TaskItem>();
        public IReadOnlyList<MetaBuild> Builds { get; private set; } = new List<MetaBuild>();
        public bool Loaded { get; private set; }
        public string LoadError { get; private set; }

        public async Task EnsureLoadedAsync()
        {
            if (Loaded) return;
            try
            {
                var tasksJson = await ReadPackagedJsonAsync("Assets\\data\\tasks_feed.json");
                var buildsJson = await ReadPackagedJsonAsync("Assets\\data\\meta_builds.json");

                var tasks = new List<TaskItem>();
                if (JsonObject.TryParse(tasksJson, out var tasksRoot) && tasksRoot.ContainsKey("tasks"))
                {
                    foreach (var item in tasksRoot["tasks"].GetArray())
                    {
                        if (item.ValueType == JsonValueType.Object)
                        {
                            tasks.Add(TaskItem.FromJson(item.GetObject()));
                        }
                    }
                }

                var builds = new List<MetaBuild>();
                if (JsonObject.TryParse(buildsJson, out var buildsRoot) && buildsRoot.ContainsKey("builds"))
                {
                    foreach (var item in buildsRoot["builds"].GetArray())
                    {
                        if (item.ValueType == JsonValueType.Object)
                        {
                            builds.Add(MetaBuild.FromJson(item.GetObject()));
                        }
                    }
                }

                Tasks = tasks;
                Builds = builds.OrderByDescending(b => b.Popularity).ToList();
                Loaded = true;
            }
            catch (Exception ex)
            {
                LoadError = ex.Message;
            }
        }

        static async Task<string> ReadPackagedJsonAsync(string relativePath)
        {
            var folder = Windows.ApplicationModel.Package.Current.InstalledLocation;
            var file = await folder.GetFileAsync(relativePath);
            return await FileIO.ReadTextAsync(file);
        }
    }
}
