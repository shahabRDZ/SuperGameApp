using System;
using System.Collections;
using UnityEngine;

namespace SuperGameApp.MiniGames.WaterSort
{
    /// <summary>
    /// Handles the liquid pouring animation between two tubes.
    /// </summary>
    public class PourAnimation : MonoBehaviour
    {
        [SerializeField] private float _liftHeight = 1.5f;
        [SerializeField] private float _liftDuration = 0.15f;
        [SerializeField] private float _moveDuration = 0.2f;
        [SerializeField] private float _pourDuration = 0.3f;
        [SerializeField] private float _tiltAngle = 60f;
        [SerializeField] private AnimationCurve _easeCurve = AnimationCurve.EaseInOut(0, 0, 1, 1);

        public bool IsAnimating { get; private set; }

        /// <summary>
        /// Animate pouring from source tube to target tube.
        /// </summary>
        public IEnumerator AnimatePour(Tube source, Tube target, Action onPourComplete)
        {
            IsAnimating = true;

            Vector3 sourceStart = source.transform.localPosition;
            Vector3 targetPos = target.transform.localPosition;

            // Step 1: Lift source tube
            Vector3 liftedPos = sourceStart + Vector3.up * _liftHeight;
            yield return MoveObject(source.transform, sourceStart, liftedPos, _liftDuration);

            // Step 2: Move above target
            Vector3 aboveTarget = new Vector3(
                targetPos.x + (sourceStart.x > targetPos.x ? 0.8f : -0.8f),
                liftedPos.y,
                liftedPos.z
            );
            yield return MoveObject(source.transform, liftedPos, aboveTarget, _moveDuration);

            // Step 3: Tilt and pour
            float tilt = sourceStart.x > targetPos.x ? _tiltAngle : -_tiltAngle;
            yield return RotateObject(source.transform, tilt, _pourDuration * 0.5f);

            // Trigger the actual data transfer at the peak of the pour
            onPourComplete?.Invoke();
            yield return new WaitForSeconds(_pourDuration * 0.5f);

            // Step 4: Untilt
            yield return RotateObject(source.transform, 0, _pourDuration * 0.3f);

            // Step 5: Return to original position
            yield return MoveObject(source.transform, source.transform.localPosition, sourceStart, _moveDuration);

            source.transform.localRotation = Quaternion.identity;
            source.transform.localPosition = sourceStart;

            IsAnimating = false;
        }

        private IEnumerator MoveObject(Transform obj, Vector3 from, Vector3 to, float duration)
        {
            float elapsed = 0;
            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                float t = _easeCurve.Evaluate(elapsed / duration);
                obj.localPosition = Vector3.Lerp(from, to, t);
                yield return null;
            }
            obj.localPosition = to;
        }

        private IEnumerator RotateObject(Transform obj, float targetZ, float duration)
        {
            Quaternion from = obj.localRotation;
            Quaternion to = Quaternion.Euler(0, 0, targetZ);
            float elapsed = 0;

            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                float t = _easeCurve.Evaluate(elapsed / duration);
                obj.localRotation = Quaternion.Lerp(from, to, t);
                yield return null;
            }
            obj.localRotation = to;
        }
    }
}
