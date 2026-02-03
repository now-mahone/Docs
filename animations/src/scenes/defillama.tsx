// Created: 2026-02-02
import {makeScene2D} from '@revideo/2d';
import {createRef, all, chain, waitFor, easeInCubic, easeOutCubic, easeInOutCubic, beginSlide, createSignal} from '@revideo/core';
import {Txt, Rect, Img, Layout, Circle, Line, Grid} from '@revideo/2d';

export default makeScene2D('defillama', function* (view: any) {
  // Refs
  const bgRef = createRef<Rect>();
  const gridRef = createRef<Grid>();
  const llamaLogoRef = createRef<Img>();
  const kerneLogoRef = createRef<Img>();
  const titleRef = createRef<Txt>();
  const subtitleRef = createRef<Txt>();
  const containerRef = createRef<Rect>();
  const badgeRef = createRef<Rect>();
  const crossRef = createRef<Txt>();
  const llamaContainerRef = createRef<Rect>();
  const kerneContainerRef = createRef<Rect>();
  const lineRef = createRef<Rect>();
  const glowRef = createRef<Circle>();

  const gridOpacity = createSignal(0);

  view.add(
    <>
      {/* Deep space background */}
      <Rect
        ref={bgRef}
        width={'100%'}
        height={'100%'}
        fill={'#050508'}
      />

      {/* Subtle animated grid */}
      <Grid
        ref={gridRef}
        width={'120%'}
        height={'120%'}
        spacing={80}
        stroke={'#1e293b'}
        lineWidth={1}
        opacity={() => gridOpacity()}
        rotation={15}
      />

      {/* Background Glow - Simplified to solid for compatibility */}
      <Circle
        ref={glowRef}
        width={800}
        height={800}
        fill={'#1e293b'}
        opacity={0}
        zIndex={-1}
      />
      
      {/* Main container */}
      <Layout ref={containerRef} layout direction={'column'} alignItems={'center'} gap={60}>
        
        {/* Logo pair with enhanced styling */}
        <Layout direction={'row'} alignItems={'center'} gap={80}>
          {/* DefiLlama Logo with Glow */}
          <Rect 
            ref={llamaContainerRef}
            radius={40} 
            clip 
            width={220} 
            height={220}
            opacity={0}
            scale={0.5}
            shadowBlur={40}
            shadowColor={'rgba(0,0,0,0.5)'}
          >
            <Img
              ref={llamaLogoRef}
              src={'/defillama-logo.jpg'}
              width={220}
            />
          </Rect>
          
          {/* Cross symbol - Animated */}
          <Txt
            ref={crossRef}
            text={"×"}
            fill={'#3b82f6'}
            fontSize={80}
            fontWeight={200}
            opacity={0}
            scale={0}
          />

          {/* Kerne Logo with Glow */}
          <Rect 
            ref={kerneContainerRef}
            radius={40} 
            fill={'#ffffff'} 
            width={220} 
            height={220}
            layout 
            alignItems={'center'} 
            justifyContent={'center'}
            opacity={0}
            scale={0.5}
            shadowBlur={60}
            shadowColor={'rgba(59, 130, 246, 0.3)'}
          >
            <Img
              ref={kerneLogoRef}
              src={'/kerne-lockup.svg'}
              width={160}
            />
          </Rect>
        </Layout>

        {/* Text Content Group */}
        <Layout direction={'column'} alignItems={'center'} gap={20}>
          <Txt
            ref={titleRef}
            text={"NOW LIVE ON DEFILLAMA"}
            fill={'#ffffff'}
            fontSize={72}
            fontWeight={800}
            letterSpacing={4}
            opacity={0}
            y={20}
          />

          {/* Animated Accent Line */}
          <Rect 
            ref={lineRef}
            width={0} 
            height={4} 
            fill={'#3b82f6'} 
            radius={2}
            shadowBlur={20}
            shadowColor={'#3b82f6'}
          />

          <Txt
            ref={subtitleRef}
            text={"DELTA-NEUTRAL YIELD INFRASTRUCTURE"}
            fill={'#94a3b8'}
            fontSize={24}
            fontWeight={600}
            letterSpacing={8}
            opacity={0}
          />
        </Layout>

        {/* Premium Badge */}
        <Rect
          ref={badgeRef}
          paddingLeft={40}
          paddingRight={40}
          paddingTop={20}
          paddingBottom={20}
          fill={'rgba(59, 130, 246, 0.1)'}
          stroke={'#3b82f6'}
          lineWidth={2}
          radius={100}
          opacity={0}
          marginTop={40}
          scale={0.9}
        >
          <Txt 
            text={"DEFILLAMA.COM/PROTOCOL/KERNE"} 
            fill={'#60a5fa'} 
            fontSize={20} 
            fontWeight={700} 
            letterSpacing={3}
          />
        </Rect>
      </Layout>
    </>
  );

  // Animation Sequence - High Energy & Premium
  yield* chain(
    // 1. Background & Grid Entrance
    all(
      gridOpacity(0.3, 1.5, easeInOutCubic),
      glowRef().opacity(1, 2, easeInOutCubic),
    ),

    // 2. Logos Impact Entrance
    all(
      llamaContainerRef().opacity(1, 0.8, easeOutCubic),
      llamaContainerRef().scale(1, 0.8, easeOutCubic),
      kerneContainerRef().opacity(1, 0.8, easeOutCubic),
      kerneContainerRef().scale(1, 0.8, easeOutCubic),
      // Subtle grid movement
      gridRef().position.y(-40, 5, easeInOutCubic),
    ),
    
    waitFor(0.1),

    // 3. Cross Pops
    all(
      crossRef().opacity(1, 0.4, easeOutCubic),
      crossRef().scale(1, 0.4, easeOutCubic),
    ),
    
    waitFor(0.2),

    // 4. Title & Line Reveal
    all(
      titleRef().opacity(1, 0.6, easeOutCubic),
      titleRef().y(0, 0.6, easeOutCubic),
      lineRef().width(600, 0.8, easeInOutCubic),
    ),
    
    waitFor(0.1),

    // 5. Subtitle & Badge
    all(
      subtitleRef().opacity(1, 0.6, easeOutCubic),
      badgeRef().opacity(1, 0.8, easeOutCubic),
      badgeRef().scale(1, 0.8, easeOutCubic),
    ),

    // 6. Subtle "Breathing" Animation
    all(
      glowRef().scale(1.2, 4, easeInOutCubic),
      kerneContainerRef().shadowBlur(80, 4, easeInOutCubic),
    ),

    waitFor(2),

    // 7. Elegant Exit
    all(
      containerRef().opacity(0, 1, easeInCubic),
      containerRef().scale(0.95, 1, easeInCubic),
      gridOpacity(0, 1, easeInCubic),
    )
  );
});
