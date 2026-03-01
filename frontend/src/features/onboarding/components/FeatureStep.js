import React from 'react';

function FeatureStep({ step }) {
  const Icon = step.icon;
  const accent = step.accent;

  return (
    <div className="onboarding-feature" data-accent={accent}>
      {/* Icon with colored glow background */}
      <div className="onboarding-icon-row">
        <div className={`onboarding-feature-icon accent-${accent}`}>
          <div className="onboarding-icon-glow" />
          <Icon size={32} strokeWidth={1.5} />
        </div>

        {/* Secondary icons */}
        {step.secondaryIcons && step.secondaryIcons.length > 0 && (
          <div className="onboarding-secondary-icons">
            {step.secondaryIcons.map((SecIcon, i) => (
              <div key={i} className={`onboarding-secondary-icon accent-${accent}`}>
                <SecIcon size={20} strokeWidth={1.5} />
              </div>
            ))}
          </div>
        )}
      </div>

      <h2 className="onboarding-feature-title">{step.title}</h2>
      <p className="onboarding-feature-desc">{step.description}</p>

      {/* Tips list */}
      {step.tips && step.tips.length > 0 && (
        <ul className="onboarding-tips">
          {step.tips.map((tip, i) => (
            <li key={i} className="onboarding-tip">
              <span className="onboarding-tip-bullet" />
              {tip}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default FeatureStep;
