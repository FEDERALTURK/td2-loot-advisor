// TD2 Loot Advisor — Xbox Companion.
// Ana masaüstü uygulamasının desteklediği 10 dille aynı liste (bkz.
// Thedivision2program/lang/*.json) — tasks_feed.json'daki çeviriler de
// tam olarak bu 10 dili kapsıyor.
using System.Collections.Generic;

namespace XboxCompanion.Services
{
    public sealed class LanguageOption
    {
        public string Code { get; }
        public string NativeName { get; }

        public LanguageOption(string code, string nativeName)
        {
            Code = code;
            NativeName = nativeName;
        }

        public override string ToString() => NativeName;

        public static readonly IReadOnlyList<LanguageOption> All = new List<LanguageOption>
        {
            new LanguageOption("tr", "Türkçe"),
            new LanguageOption("en", "English"),
            new LanguageOption("de", "Deutsch"),
            new LanguageOption("fr", "Français"),
            new LanguageOption("es", "Español"),
            new LanguageOption("it", "Italiano"),
            new LanguageOption("pt", "Português"),
            new LanguageOption("ru", "Русский"),
            new LanguageOption("pl", "Polski"),
            new LanguageOption("nl", "Nederlands"),
        };
    }
}
