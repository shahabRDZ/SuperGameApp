using UnityEngine;
using SuperGameApp.Core.Utils;

namespace SuperGameApp.Core.Managers
{
    /// <summary>
    /// Handles music and SFX playback with volume control.
    /// </summary>
    public class AudioManager : Singleton<AudioManager>
    {
        [SerializeField] private AudioSource _musicSource;
        [SerializeField] private AudioSource _sfxSource;

        [Header("Common SFX")]
        [SerializeField] private AudioClip _buttonClick;
        [SerializeField] private AudioClip _coinCollect;
        [SerializeField] private AudioClip _levelComplete;
        [SerializeField] private AudioClip _levelFail;

        protected override void Awake()
        {
            base.Awake();

            if (_musicSource == null)
            {
                _musicSource = gameObject.AddComponent<AudioSource>();
                _musicSource.loop = true;
                _musicSource.playOnAwake = false;
            }

            if (_sfxSource == null)
            {
                _sfxSource = gameObject.AddComponent<AudioSource>();
                _sfxSource.loop = false;
                _sfxSource.playOnAwake = false;
            }
        }

        public void SetMusicVolume(float volume)
        {
            _musicSource.volume = volume;
            SaveManager.Instance.Data.MusicVolume = volume;
            SaveManager.Instance.Save();
        }

        public void SetSfxVolume(float volume)
        {
            _sfxSource.volume = volume;
            SaveManager.Instance.Data.SfxVolume = volume;
            SaveManager.Instance.Save();
        }

        public void PlayMusic(AudioClip clip)
        {
            if (_musicSource.clip == clip && _musicSource.isPlaying) return;
            _musicSource.clip = clip;
            _musicSource.volume = SaveManager.Instance.Data.MusicVolume;
            _musicSource.Play();
        }

        public void StopMusic() => _musicSource.Stop();

        public void PlaySfx(AudioClip clip)
        {
            if (clip == null) return;
            _sfxSource.volume = SaveManager.Instance.Data.SfxVolume;
            _sfxSource.PlayOneShot(clip);
        }

        public void PlayButtonClick() => PlaySfx(_buttonClick);
        public void PlayCoinCollect() => PlaySfx(_coinCollect);
        public void PlayLevelComplete() => PlaySfx(_levelComplete);
        public void PlayLevelFail() => PlaySfx(_levelFail);
    }
}
