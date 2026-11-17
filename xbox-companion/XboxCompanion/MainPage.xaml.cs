// TD2 Loot Advisor — Xbox Companion — ana sayfa.
// Gömülü veriyi (DataService) yükler, dil seçimine göre listeleri doldurur.
// Canlı ekran okuma/overlay YOK — bkz. proje köküne yakın README ve
// docs/console_game_caption_roadmap.md §3a Alt-aşama ayrımı.
using System.Collections.Generic;
using System.Linq;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;
using XboxCompanion.Models;
using XboxCompanion.Services;

namespace XboxCompanion
{
    public sealed partial class MainPage : Page
    {
        readonly DataService _data = new DataService();

        public MainPage()
        {
            InitializeComponent();
            Loaded += OnPageLoaded;
        }

        async void OnPageLoaded(object sender, RoutedEventArgs e)
        {
            StatusText.Text = "Veriler yükleniyor…";
            LanguagePicker.ItemsSource = LanguageOption.All;
            LanguagePicker.SelectedIndex = 0; // tr

            await _data.EnsureLoadedAsync();

            if (!_data.Loaded)
            {
                StatusText.Text = "Veri yüklenemedi: " + _data.LoadError;
                return;
            }

            RefreshLists();
            StatusText.Text = $"{_data.Tasks.Count} görev · {_data.Builds.Count} build — sürüm içine gömülü, çevrimdışı";
        }

        void OnLanguageChanged(object sender, SelectionChangedEventArgs e)
        {
            if (_data.Loaded) RefreshLists();
        }

        string SelectedLang => (LanguagePicker.SelectedItem as LanguageOption)?.Code ?? "tr";

        void RefreshLists()
        {
            var lang = SelectedLang;

            TasksList.ItemsSource = _data.Tasks.Select(t => new TaskDisplayItem
            {
                CategoryLabel = CategoryLabel(t.Category),
                Text = t.TextFor(lang) ?? "(çeviri yok)",
                How = t.HowFor(lang),
                HowVisibility = string.IsNullOrWhiteSpace(t.HowFor(lang)) ? Visibility.Collapsed : Visibility.Visible,
            }).ToList();

            BuildsList.ItemsSource = _data.Builds.Select(b => new BuildDisplayItem
            {
                Name = b.Name,
                SubLine = SubLine(b),
                PopularityLabel = b.Popularity > 0 ? $"★ {b.Popularity}" : "",
                Summary = b.SummaryFor(lang) ?? "",
            }).ToList();
        }

        static string CategoryLabel(string cat)
        {
            switch (cat)
            {
                case "manhunt": return "MANHUNT";
                case "journey": return "JOURNEY";
                default: return string.IsNullOrEmpty(cat) ? "GÖREV" : cat.ToUpperInvariant();
            }
        }

        static string SubLine(MetaBuild b)
        {
            var parts = new List<string>();
            if (!string.IsNullOrEmpty(b.Mode)) parts.Add(b.Mode);
            if (!string.IsNullOrEmpty(b.Role)) parts.Add(b.Role.ToUpperInvariant());
            if (b.SetsOrBrands.Count > 0) parts.Add(string.Join(" / ", b.SetsOrBrands));
            if (b.SetBonus > 0) parts.Add($"{b.SetBonus} parça set");
            return string.Join("  ·  ", parts);
        }

        sealed class TaskDisplayItem
        {
            public string CategoryLabel { get; set; }
            public string Text { get; set; }
            public string How { get; set; }
            public Visibility HowVisibility { get; set; }
        }

        sealed class BuildDisplayItem
        {
            public string Name { get; set; }
            public string SubLine { get; set; }
            public string PopularityLabel { get; set; }
            public string Summary { get; set; }
        }
    }
}
