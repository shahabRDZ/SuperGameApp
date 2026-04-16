using System.Collections.Generic;
using UnityEngine;
using WaterSort.Core;

namespace WaterSort.Game
{
    public class Bottle : MonoBehaviour
    {
        [Header("Layer Renderers (bottom to top)")]
        [SerializeField] private SpriteRenderer[] layerRenderers = new SpriteRenderer[4];

        [Header("Visual")]
        [SerializeField] private SpriteRenderer bottleBody;
        [SerializeField] private SpriteRenderer glowRenderer;
        [SerializeField] private GameObject completeBadge;
        [SerializeField] private ParticleSystem completeParticles;

        private List<int> _layers = new List<int>();
        private bool _selected;
        private Vector3 _originalPos;
        private float _bounceTime = -1f;

        public int Index { get; private set; }
        public bool IsEmpty => _layers.Count == 0;
        public bool IsFull => _layers.Count >= 4;
        public int TopColor => _layers.Count > 0 ? _layers[_layers.Count - 1] : 0;
        public bool IsComplete => LevelGenerator.IsComplete(_layers);

        public int TopColorCount
        {
            get
            {
                if (_layers.Count == 0) return 0;
                int top = TopColor, count = 0;
                for (int i = _layers.Count - 1; i >= 0 && _layers[i] == top; i--) count++;
                return count;
            }
        }

        public void Init(int index, List<int> layers)
        {
            Index = index;
            _layers = new List<int>(layers);
            _originalPos = transform.localPosition;
            _selected = false;
            if (glowRenderer) glowRenderer.enabled = false;
            if (completeBadge) completeBadge.SetActive(false);
            UpdateVisual();
        }

        public bool CanReceive(int color)
        {
            if (IsFull) return false;
            if (IsEmpty) return true;
            return TopColor == color;
        }

        public int[] RemoveTop()
        {
            if (IsEmpty) return new int[0];
            int top = TopColor;
            var removed = new List<int>();
            while (_layers.Count > 0 && _layers[_layers.Count - 1] == top)
            {
                removed.Add(top);
                _layers.RemoveAt(_layers.Count - 1);
            }
            UpdateVisual();
            return removed.ToArray();
        }

        public void AddLayers(int[] colors)
        {
            foreach (int c in colors)
                if (_layers.Count < 4)
                    _layers.Add(c);
            UpdateVisual();

            if (IsComplete && completeParticles != null)
            {
                var main = completeParticles.main;
                main.startColor = ColorPalette.GetLiquidColor(_layers[0]);
                completeParticles.Play();
            }
        }

        public List<int> GetState() => new List<int>(_layers);

        public void SetState(List<int> state)
        {
            _layers = new List<int>(state);
            UpdateVisual();
        }

        public void SetSelected(bool selected)
        {
            _selected = selected;
            if (glowRenderer)
            {
                glowRenderer.enabled = selected;
                glowRenderer.color = new Color32(70, 150, 255, 80);
            }

            if (selected)
            {
                _bounceTime = 0;
            }
            else
            {
                transform.localPosition = _originalPos;
                _bounceTime = -1;
            }
        }

        public void SetHintHighlight(bool on)
        {
            if (glowRenderer)
            {
                glowRenderer.enabled = on;
                if (on) glowRenderer.color = new Color32(255, 220, 80, 80);
            }
        }

        private void Update()
        {
            // Bounce animation
            if (_bounceTime >= 0)
            {
                _bounceTime += Time.deltaTime * 6f;
                float bounce = Mathf.Sin(Mathf.Min(Mathf.PI, _bounceTime)) * 0.3f;
                transform.localPosition = _originalPos + Vector3.up * bounce;
            }

            // Complete badge
            if (completeBadge) completeBadge.SetActive(IsComplete);

            // Complete glow
            if (IsComplete && glowRenderer && !_selected)
            {
                glowRenderer.enabled = true;
                glowRenderer.color = new Color32(80, 200, 120, 60);
            }
        }

        private void UpdateVisual()
        {
            for (int i = 0; i < 4; i++)
            {
                if (i < layerRenderers.Length && layerRenderers[i] != null)
                {
                    if (i < _layers.Count)
                    {
                        layerRenderers[i].enabled = true;
                        layerRenderers[i].color = ColorPalette.GetLiquidColor(_layers[i]);
                    }
                    else
                    {
                        layerRenderers[i].enabled = false;
                    }
                }
            }
        }

        private void OnMouseDown()
        {
            GameManager.Instance.OnBottleClicked(this);
        }
    }
}
