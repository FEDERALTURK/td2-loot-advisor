// TD2 Loot Advisor — Xbox Companion.
// Standart UWP uygulama önyükleme kodu (Visual Studio'nun klasik "Blank App
// (Universal Windows)" şablonuyla aynı iskelet) — özel mantık MainPage'de.
using Windows.ApplicationModel.Activation;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;
using Windows.UI.Xaml.Navigation;

namespace XboxCompanion
{
    sealed partial class App : Application
    {
        public App()
        {
            InitializeComponent();
            Suspending += OnSuspending;
        }

        protected override void OnLaunched(LaunchActivatedEventArgs e)
        {
            Frame rootFrame = Window.Current.Content as Frame;

            if (rootFrame == null)
            {
                rootFrame = new Frame();
                rootFrame.NavigationFailed += OnNavigationFailed;
                Window.Current.Content = rootFrame;
            }

            if (e.PrelaunchActivated == false)
            {
                if (rootFrame.Content == null)
                {
                    rootFrame.Navigate(typeof(MainPage), e.Arguments);
                }
                Window.Current.Activate();
            }
        }

        void OnNavigationFailed(object sender, NavigationFailedEventArgs e)
        {
            throw new System.Exception("Sayfa yüklenemedi: " + e.SourcePageType.FullName);
        }

        void OnSuspending(object sender, Windows.ApplicationModel.SuspendingEventArgs e)
        {
            // Bu uygulama gömülü JSON'dan okunan değişmez veriyle çalışıyor;
            // askıya alma öncesi kaydedilecek bir durum yok.
        }
    }
}
