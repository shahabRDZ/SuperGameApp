using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

namespace SuperGameApp.MiniGames.WaterSort
{
    /// <summary>
    /// Represents a single tube in the Water Sort puzzle.
    /// Handles visual display and touch interaction.
    /// </summary>
    public class Tube : MonoBehaviour, IPointerClickHandler
    {
        [SerializeField] private Transform _liquidContainer;
        [SerializeField] private GameObject _liquidLayerPrefab;
        [SerializeField] private SpriteRenderer _tubeSprite;
        [SerializeField] private float _layerHeight = 0.5f;
        [SerializeField] private float _selectedYOffset = 0.5f;

        private List<int> _layers = new List<int>();
        private List<GameObject> _layerObjects = new List<GameObject>();
        private int _maxLayers = 4;
        private bool _isSelected;
        private Vector3 _originalPosition;

        public int TubeIndex { get; private set; }
        public int LayerCount => _layers.Count;
        public bool IsEmpty => _layers.Count == 0;
        public bool IsFull => _layers.Count >= _maxLayers;

        public int TopColor => _layers.Count > 0 ? _layers[_layers.Count - 1] : 0;

        public bool IsComplete
        {
            get
            {
                if (_layers.Count != _maxLayers) return false;
                int first = _layers[0];
                for (int i = 1; i < _layers.Count; i++)
                    if (_layers[i] != first) return false;
                return true;
            }
        }

        public void Initialize(int tubeIndex, int maxLayers, int[] initialLayers)
        {
            TubeIndex = tubeIndex;
            _maxLayers = maxLayers;
            _originalPosition = transform.localPosition;

            _layers.Clear();
            foreach (int layer in initialLayers)
            {
                if (layer > 0)
                    _layers.Add(layer);
            }

            RefreshVisual();
        }

        public int TopColorCount()
        {
            if (_layers.Count == 0) return 0;
            int count = 0;
            int top = TopColor;
            for (int i = _layers.Count - 1; i >= 0; i--)
            {
                if (_layers[i] == top) count++;
                else break;
            }
            return count;
        }

        public bool CanReceive(int color, int amount)
        {
            if (_layers.Count + amount > _maxLayers) return false;
            if (_layers.Count == 0) return true;
            return TopColor == color;
        }

        public int[] RemoveTopLayers()
        {
            if (_layers.Count == 0) return new int[0];

            int topColor = TopColor;
            var removed = new List<int>();

            while (_layers.Count > 0 && _layers[_layers.Count - 1] == topColor)
            {
                removed.Add(_layers[_layers.Count - 1]);
                _layers.RemoveAt(_layers.Count - 1);
            }

            RefreshVisual();
            return removed.ToArray();
        }

        public void AddLayers(int[] layers)
        {
            foreach (int l in layers)
                _layers.Add(l);
            RefreshVisual();
        }

        public void SetSelected(bool selected)
        {
            _isSelected = selected;
            var pos = _originalPosition;
            if (selected) pos.y += _selectedYOffset;
            transform.localPosition = pos;
        }

        public void OnPointerClick(PointerEventData eventData)
        {
            WaterSortGameManager.Instance.OnTubeClicked(this);
        }

        public int[] GetCurrentState()
        {
            return _layers.ToArray();
        }

        public void RestoreState(int[] state)
        {
            _layers.Clear();
            _layers.AddRange(state);
            RefreshVisual();
        }

        private void RefreshVisual()
        {
            foreach (var obj in _layerObjects)
                Destroy(obj);
            _layerObjects.Clear();

            for (int i = 0; i < _layers.Count; i++)
            {
                var layerObj = Instantiate(_liquidLayerPrefab, _liquidContainer);
                layerObj.transform.localPosition = new Vector3(0, i * _layerHeight, 0);

                var renderer = layerObj.GetComponent<SpriteRenderer>();
                if (renderer != null)
                    renderer.color = WaterSortGameManager.Instance.GetColor(_layers[i]);

                _layerObjects.Add(layerObj);
            }
        }
    }
}
