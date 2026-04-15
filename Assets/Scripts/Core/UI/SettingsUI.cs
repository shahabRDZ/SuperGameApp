using UnityEngine;
using UnityEngine.UI;
using SuperGameApp.Core.Managers;
using SuperGameApp.Core.Events;

namespace SuperGameApp.Core.UI
{
    /// <summary>
    /// Settings panel for music, SFX, theme, and language.
    /// </summary>
    public class SettingsUI : MonoBehaviour
    {
        [SerializeField] private Slider _musicSlider;
        [SerializeField] private Slider _sfxSlider;
        [SerializeField] private Toggle _darkThemeToggle;
        [SerializeField] private Button _closeButton;

        private void OnEnable()
        {
            var data = SaveManager.Instance.Data;
            _musicSlider.value = data.MusicVolume;
            _sfxSlider.value = data.SfxVolume;
            _darkThemeToggle.isOn = data.IsDarkTheme;

            _musicSlider.onValueChanged.AddListener(OnMusicChanged);
            _sfxSlider.onValueChanged.AddListener(OnSfxChanged);
            _darkThemeToggle.onValueChanged.AddListener(OnThemeChanged);
            _closeButton.onClick.AddListener(Close);
        }

        private void OnDisable()
        {
            _musicSlider.onValueChanged.RemoveListener(OnMusicChanged);
            _sfxSlider.onValueChanged.RemoveListener(OnSfxChanged);
            _darkThemeToggle.onValueChanged.RemoveListener(OnThemeChanged);
            _closeButton.onClick.RemoveListener(Close);
        }

        private void OnMusicChanged(float value) => AudioManager.Instance.SetMusicVolume(value);
        private void OnSfxChanged(float value) => AudioManager.Instance.SetSfxVolume(value);

        private void OnThemeChanged(bool isDark)
        {
            SaveManager.Instance.Data.IsDarkTheme = isDark;
            SaveManager.Instance.Save();
            GameEvents.FireSettingsChanged();
        }

        private void Close()
        {
            AudioManager.Instance.PlayButtonClick();
            UIManager.Instance.HidePanel(gameObject);
        }
    }
}
