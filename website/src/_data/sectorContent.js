// Authored sector-page copy for the two per-sector gapped fields:
// `workedExample` and `ctaRoles`. Written to the sector rewrite brief
// (2026-07-23). The other two fields — sources and related-projects — are
// patterns/derivations and live in the template + catalog.js, not here.
//
// WORKED-EXAMPLE RULES (brief §2), enforced in every entry below:
//  - Method mood, not findings: every step is what the work WOULD look like.
//    No cost, percentage, ratio, or reduction figure appears anywhere.
//  - The six step verbs are fixed: Measure · Publish · Break down · Match ·
//    Package · Track.
//  - The Match step names a mechanism drawn from THAT sector's dossier
//    `Opportunity` field — nothing outside it.
//  - No claim a mechanism works ("could" is a hypothesis; "cuts" is a finding).
//  - Step 6 always carries the negative-result commitment.
//  - Uncost does not own or operate the thing; step 5 names who would run it.
//
//  workedExample: null means the field stays gapped. The four research-gated
//  sectors (Healthcare, Care, Education, Safety) are gapped deliberately: their
//  dossier guardrails forbid patient-facing / child-facing / enforcement work
//  without qualified governance, so a "a community group can run it" worked
//  example (step 5) would imply a service those guardrails do not permit. Their
//  interventions stay future-study; only cost measurement is in scope today.

const PUBLISH =
  "Publish — put the sources and the assumptions up before the conclusions, so anyone can check the starting point.";

module.exports = {
  food: {
    workedExample: {
      scenario: "A worked example: fresh produce in a dense city.",
      steps: [
        "Measure — start with what a household in one region actually spends on fresh produce, from public data, with the date and region attached.",
        PUBLISH,
        "Break down — separate that price into its parts. For produce, that likely means land, energy, labour, water and logistics; establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. A controlled-environment farm uses AI for climate, light and nutrients and robotics to plant, tend and harvest. It could reduce transport and spoilage. It also adds energy, capital and maintenance costs. Both sides get counted.",
        "Package — publish the model, the sources, a project brief and a playbook, so a community group, co-op, school or nonprofit can run it. Uncost does not own the farm.",
        "Track — follow whether the total cost actually falls where the model is applied. If energy, capital and maintenance outweigh the saving, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "food-systems and agriculture research"],
  },

  water: {
    workedExample: {
      scenario: "A worked example: water lost to leaks in an ageing network.",
      steps: [
        "Measure — start with what a community actually pays for water in one region, and how much supply is lost before it reaches a tap, from public utility data with the date and region attached.",
        PUBLISH,
        "Break down — separate the cost into treatment, pumping, network maintenance and losses. For an ageing network, leaks may be a large share; establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. Sensors and leak detection could locate losses sooner, and automated maintenance could shorten repairs. Both could cut waste, and both add hardware, power and upkeep costs. Both sides get counted.",
        "Package — publish the model, the sources, a brief and a playbook, so a utility, municipality or community operator can run it under local regulation and qualified operators. Uncost does not run the network.",
        "Track — follow whether the total cost actually falls where the model is applied. Where sensing and maintenance cost more than the water they save, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "water and utilities research"],
  },

  shelter: {
    workedExample: {
      scenario: "A worked example: the cost of a modest new home.",
      steps: [
        "Measure — start with what a modest home actually costs to build and run in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into land, entitlement and permitting, finance, materials, labour, and the heating and cooling it will need for years. Establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. Modular design and construction-automation support could reduce labour and waste, and permitting tools could shorten entitlement. Land, finance, code and safety constraints do not move and stay visible. Both sides get counted.",
        "Package — publish the model, the sources, a brief and a playbook, so a housing nonprofit, co-op or public body can run it. Uncost does not build the homes.",
        "Track — follow whether the total cost actually falls where the model is applied. Where automation does not beat conventional construction once finance and code are counted, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "housing and construction-cost research"],
  },

  energy: {
    workedExample: {
      scenario: "A worked example: a neighbourhood's electricity bill.",
      steps: [
        "Measure — start with what a household actually pays for electricity and heat in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate the bill into generation, grid and delivery, fuel, and peak demand. Establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. Shared solar with batteries and load management, planned as a microgrid, could reduce fuel and peak costs. It also carries capital, inspection and maintenance costs across its full lifecycle. Both sides get counted, on local-grid assumptions, with no single-number savings promise.",
        "Package — publish the model, the sources, a brief and a playbook, so a community energy group, co-op or public body can run it. Uncost does not operate the microgrid.",
        "Track — follow whether the total cost actually falls where the model is applied. Where the lifecycle cost outweighs the saving, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "energy-systems research"],
  },

  healthcare: {
    workedExample: {
      measurement: true,
      steps: [
        "Measure — start with what a household actually spends on medicine, diagnostics and basic care in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into its parts: prevention, diagnostics, medicine, and the visits that go with them. Establishing the real split is the work, not the assumption.",
      ],
      stopBetween: "health and their care",
      stopReason: "qualified clinical, legal, privacy and safety governance",
    },
    ctaRoles: ["source and licence review", "data methodology", "health-economics research (cost measurement only)"],
  },
  care: {
    workedExample: {
      measurement: true,
      steps: [
        "Measure — start with what a household actually spends on childcare, eldercare and disability care in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into its parts: the hours of care, the people who provide it, and the support families pay for around it. Establishing the real split is the work, not the assumption.",
      ],
      stopBetween: "care",
      stopReason: "dignity, consent, privacy, safeguarding and human oversight",
    },
    ctaRoles: ["source and licence review", "data methodology", "care-economics research"],
  },
  education: {
    workedExample: {
      measurement: true,
      steps: [
        "Measure — start with what a household actually spends on education, tutoring and skills in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into its parts: tuition and fees, materials, tutoring, and the time it takes. Establishing the real split is the work, not the assumption.",
      ],
      stopBetween: "child's education",
      stopReason: "privacy, curriculum, bias, guardian-consent and human-oversight safeguards",
    },
    ctaRoles: ["source and licence review", "data methodology", "education-cost research"],
  },

  transportation: {
    workedExample: {
      scenario: "A worked example: getting around without a car.",
      steps: [
        "Measure — start with what getting to work, school and shops actually costs a household in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into vehicles, fuel, insurance, transit fares, and the time lost to poor connections. Establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. Route optimisation and shared fleets could raise the use of each vehicle, and — where lawful and safe — delivery robotics or an autonomous shuttle could lower last-mile costs. Jurisdiction, safety, insurance, accessibility and operator review do not move and stay visible. Both sides get counted.",
        "Package — publish the model, the sources, a brief and a playbook, so a transit agency, co-op or community operator can run it under the required jurisdiction and operator review. Uncost does not run the service.",
        "Track — follow whether the total cost actually falls where the model is applied. Where a shared or automated option does not beat the status quo once insurance and safety are counted, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "transport and mobility research"],
  },

  clothing: {
    workedExample: {
      scenario: "A worked example: the yearly cost of clothing a family.",
      steps: [
        "Measure — start with what clothing a family actually costs over a year in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into new garments, footwear, laundry, and replacement driven by wear. Establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. Repair services, textile recycling, shared laundry and local production could extend garment life and cut replacement. Each carries labour, material and energy costs of its own, verified rather than assumed. Both sides get counted.",
        "Package — publish the model, the sources, a brief and a playbook, so a community group, co-op or social enterprise can run it. Uncost does not run the workshop.",
        "Track — follow whether the total cost actually falls where the model is applied. Where repair or local production does not beat replacement once labour and energy are counted, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "textile and repair research"],
  },

  goods: {
    workedExample: {
      scenario: "A worked example: the drill used twelve minutes a year.",
      steps: [
        "Measure — start with what a household actually spends on tools, appliances and household goods it rarely uses, in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into purchase, storage, and the low use that makes owning expensive per hour. Establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. A tool library with repair systems and shared-access software could raise the use of each item and cut what a household must buy. It also carries liability, storage, maintenance, insurance and governance costs. Both sides get counted.",
        "Package — publish the model, the sources, a brief and a playbook, so a library, co-op or community group can run it. Uncost does not run the library.",
        "Track — follow whether the total cost actually falls where the model is applied. Where the running costs of sharing outweigh the saving, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "shared-access and repair research"],
  },

  materials: {
    workedExample: {
      scenario: "A worked example: what a community throws away.",
      steps: [
        "Measure — start with what a community actually pays to buy materials and to dispose of waste in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into raw inputs, transport, and disposal, and how much of the waste stream could be recovered. Establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. Sorting robotics, recovery and reusable parts could turn part of the waste stream into local production inputs. Energy, contamination, transport, market demand and disposal all carry costs of their own. Both sides get counted.",
        "Package — publish the model, the sources, a brief and a playbook, so a recycler, municipality or co-op can run it. Uncost does not run the facility.",
        "Track — follow whether the total cost actually falls where the model is applied. Where recovery costs more than it returns once energy and contamination are counted, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "materials and recycling research"],
  },

  communication: {
    workedExample: {
      scenario: "A worked example: getting a household online.",
      steps: [
        "Measure — start with what a household actually pays for internet access and devices in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into connectivity, devices, and the ongoing service and support that keep them working. Establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. A low-cost community network, open devices and connectivity planning could lower access costs. Privacy, accessibility, security and the ongoing service cost stay explicit, not assumed away. Both sides get counted.",
        "Package — publish the model, the sources, a brief and a playbook, so a community network, library or co-op can run it. Uncost does not run the network.",
        "Track — follow whether the total cost actually falls where the model is applied. Where a community network does not beat existing access once support and security are counted, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "connectivity and access research"],
  },

  safety: {
    workedExample: {
      measurement: true,
      steps: [
        "Measure — start with what a household and a community actually spend on emergency readiness and prevention in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into its parts: prevention, emergency response, disaster readiness, and recovery. Establishing the real split is the work, not the assumption.",
      ],
      stopBetween: "safety",
      stopReason: "qualified authorities, safeguards, and a firm line that it is never enforcement or surveillance",
    },
    ctaRoles: ["source and licence review", "data methodology", "community-resilience research"],
  },

  environment: {
    workedExample: {
      scenario: "A worked example: the local cost of a degraded commons.",
      steps: [
        "Measure — start with a cost a community already bears from a degraded local environment in one region — money spent on, say, flood damage or waste handling — from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into its parts, and be explicit about what is measured versus inferred. Establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. Sensing, waste reduction and restoration work could reduce some of those costs. Ecological benefit is stated with its uncertainty, and causality is not overstated. Both sides get counted.",
        "Package — publish the model, the sources, a brief and a playbook, so a community group, land trust or public body can run it. Uncost does not run the restoration.",
        "Track — follow whether the measured cost actually falls where the model is applied. Where an intervention cannot be shown to help, or the uncertainty is too wide to claim it, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "environmental-cost research"],
  },

  leisure: {
    workedExample: {
      scenario: "A worked example: the cost of taking part.",
      steps: [
        "Measure — start with what taking part in recreation, sport and culture actually costs a household in one region, from public data with the date and region attached.",
        PUBLISH,
        "Break down — separate that cost into equipment, venue and membership fees, and access. Establishing the real split is the work, not the assumption.",
        "Match — ask which parts a named mechanism could move. Shared equipment, open cultural tools and accessible public spaces could lower the cost of participation. Access, safety, copyright, community control and maintenance stay visible. Both sides get counted.",
        "Package — publish the model, the sources, a brief and a playbook, so a community group, library or public body can run it. Uncost does not run the space.",
        "Track — follow whether the total cost actually falls where the model is applied. Where a shared option does not lower the real cost of taking part once maintenance is counted, that result gets published with the same prominence as a win.",
      ],
    },
    ctaRoles: ["source and licence review", "data methodology", "public-space and culture research"],
  },
};
