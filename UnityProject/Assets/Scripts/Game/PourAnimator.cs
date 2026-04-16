using System;
using System.Collections;
using UnityEngine;

namespace WaterSort.Game
{
    public class PourAnimator : MonoBehaviour
    {
        [SerializeField] private float liftHeight = 1.2f;
        [SerializeField] private float liftDuration = 0.15f;
        [SerializeField] private float slideDuration = 0.18f;
        [SerializeField] private float tiltAngle = 55f;
        [SerializeField] private float tiltDuration = 0.25f;
        [SerializeField] private float returnDuration = 0.2f;
        [SerializeField] private AnimationCurve easeCurve = AnimationCurve.EaseInOut(0, 0, 1, 1);

        [Header("Stream")]
        [SerializeField] private ParticleSystem streamParticles;

        public bool IsAnimating { get; private set; }

        public IEnumerator AnimatePour(Bottle source, Bottle target, Action onPour)
        {
            IsAnimating = true;

            Vector3 startPos = source.transform.localPosition;
            Vector3 targetPos = target.transform.localPosition;
            float direction = startPos.x > targetPos.x ? 1f : -1f;

            // Phase 1: Lift
            Vector3 liftedPos = startPos + Vector3.up * liftHeight;
            yield return Move(source.transform, startPos, liftedPos, liftDuration);

            // Phase 2: Slide above target
            Vector3 aboveTarget = new Vector3(
                targetPos.x + direction * 0.4f,
                liftedPos.y,
                liftedPos.z
            );
            yield return Move(source.transform, liftedPos, aboveTarget, slideDuration);

            // Phase 3: Tilt and pour
            float tilt = -direction * tiltAngle;

            // Start stream particles
            if (streamParticles)
            {
                streamParticles.transform.position = source.transform.position;
                streamParticles.Play();
            }

            yield return Tilt(source.transform, tilt, tiltDuration * 0.5f);

            // Execute pour at peak tilt
            onPour?.Invoke();

            yield return new WaitForSeconds(tiltDuration * 0.3f);

            // Stop stream
            if (streamParticles) streamParticles.Stop();

            // Phase 4: Untilt
            yield return Tilt(source.transform, 0, tiltDuration * 0.3f);

            // Phase 5: Return
            yield return Move(source.transform, source.transform.localPosition, startPos, returnDuration);

            source.transform.localPosition = startPos;
            source.transform.localRotation = Quaternion.identity;

            IsAnimating = false;
        }

        private IEnumerator Move(Transform obj, Vector3 from, Vector3 to, float dur)
        {
            float elapsed = 0;
            while (elapsed < dur)
            {
                elapsed += Time.deltaTime;
                float t = easeCurve.Evaluate(Mathf.Clamp01(elapsed / dur));
                obj.localPosition = Vector3.Lerp(from, to, t);
                yield return null;
            }
            obj.localPosition = to;
        }

        private IEnumerator Tilt(Transform obj, float targetZ, float dur)
        {
            Quaternion from = obj.localRotation;
            Quaternion to = Quaternion.Euler(0, 0, targetZ);
            float elapsed = 0;
            while (elapsed < dur)
            {
                elapsed += Time.deltaTime;
                float t = easeCurve.Evaluate(Mathf.Clamp01(elapsed / dur));
                obj.localRotation = Quaternion.Lerp(from, to, t);
                yield return null;
            }
            obj.localRotation = to;
        }
    }
}
