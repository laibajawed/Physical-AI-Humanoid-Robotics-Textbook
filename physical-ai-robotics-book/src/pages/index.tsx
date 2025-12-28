import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';

import clsx from 'clsx';

function HomepageHeroSection() {
  return (
    <section className="hero-section" aria-labelledby="hero-title">
      <div className="hero-text-section flex flex-col justify-center items-center text-center">
        <div className="flex items-center space-x-6 mb-10">
          <h1 id="hero-title" className="text-[6rem] font-bold gradient-text leading-tight">
            Think
          </h1>
          <span className="text-[6rem] font-bold mx-6">→</span>
          <h1 className="text-[6rem] font-bold gradient-text leading-tight">Move</h1>
          <span className="text-[6rem] font-bold mx-6">→</span>
          <h1 className="text-[6rem] font-bold gradient-text leading-tight">Learn</h1>
        </div>
        <h2 className="text-3xl text-white my-6 max-w-2xl">
          The Complete Handbook for Humanoid Intelligence
        </h2>
        <p className="text-xl text-gray-300 mb-8 max-w-3xl">
          Master ROS 2, NVIDIA Isaac Sim, Vision-Language-Action models, and embodied foundation models — all open-source and production-ready.
        </p>
        <Link
          to="/docs/introduction"
          className="cta-button focusable"
          aria-label="Start building - Go to the introduction of the Physical AI & Humanoid Robotics textbook"
        >
          Start Building →
        </Link>
      </div>
    </section>
  );
}

function getModulePath(index: number): string {
  const modulePaths = [
    '/docs/module1-ros2-fundamentals/chapter1-ros2-basics',
    '/docs/module2-simulation-gazebo-unity/chapter4-gazebo-simulation',
    '/docs/module3-advanced-robotics-nvidia-isaac/chapter7-isaac-sdk',
    '/docs/module4-vla-systems/chapter9-vision-language'
  ];
  return modulePaths[index] || '/docs/intro';
}

function ModuleCard({ title, description, index }: { title: string, description: string, index: number }) {
  return (
    <div className="module-card p-6 flex flex-col items-center text-center h-full" role="region" aria-labelledby={`module-title-${index}`}>
      <div className="flex flex-col items-center text-center flex-grow flex-shrink">
        <h3 id={`module-title-${index}`} className="text-xl font-bold text-white mb-3">{title}</h3>
        <p id={`module-desc-${index}`} className="text-gray-300 mb-4">{description}</p>
      </div>
      <Link
        to={getModulePath(index)}
        className="inline-block px-4 py-3 bg-white text-gray-900 rounded-full text-sm font-medium hover:bg-gray-200 transition-colors focusable mt-auto"
        aria-describedby={`module-desc-${index}`}
      >
        Explore Module
      </Link>
    </div>
  );
}

function ModuleGrid() {
  const modules = [
    {
      title: "The Nervous System (ROS 2) →",
      description: "Foundations of modern robot operating systems"
    },
    {
      title: "Digital Twins (Simulation) →",
      description: "Photorealistic simulation with Gazebo, Unity & Isaac Sim"
    },
    {
      title: "The AI Brain (NVIDIA Isaac) →",
      description: "End-to-end GPU-accelerated robotics development"
    },
    {
      title: "Vision-Language-Action (VLA) →",
      description: "Embodied foundation models that see, reason, and act"
    }
  ];

  return (
    <section className="module-grid">
      {modules.map((module, index) => (
        <ModuleCard
          key={index}
          title={module.title}
          description={module.description}
          index={index}
        />
      ))}
    </section>
  );
}

export default function Home(): React.ReactNode {
  return (
    <Layout
      title="Physical AI & Humanoid Robotics"
      description="The Complete Handbook for Humanoid Intelligence - Master ROS 2, NVIDIA Isaac Sim, Vision-Language-Action models, and embodied foundation models">
      <main className="min-h-screen" style={{ backgroundColor: '#0F0F1A' }}>
        <div className="container mx-auto px-4 py-44">
          <HomepageHeroSection />
          <ModuleGrid />
        </div>
      </main>
    </Layout>
  );
}
