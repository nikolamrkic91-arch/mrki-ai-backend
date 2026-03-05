// Copyright Epic Games, Inc. All Rights Reserved.

#include "{{class_name}}.h"

// Sets default values
A{{class_name}}::A{{class_name}}()
{
    // Set this actor to call Tick() every frame
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = TickInterval;

    // Create default scene root
    DefaultSceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("DefaultSceneRoot"));
    RootComponent = DefaultSceneRoot;
}

// Called when the game starts or when spawned
void A{{class_name}}::BeginPlay()
{
    Super::BeginPlay();

    OnBeginPlay();

    if (bAutoActivate)
    {
        Activate();
    }
}

void A{{class_name}}::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (bIsActive)
    {
        Deactivate();
    }

    Super::EndPlay(EndPlayReason);
}

// Called every frame
void A{{class_name}}::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    if (bIsActive)
    {
        OnUpdate(DeltaTime);
    }
}

void A{{class_name}}::OnActivated_Implementation()
{
    // Override in Blueprint or derived class
}

void A{{class_name}}::OnDeactivated_Implementation()
{
    // Override in Blueprint or derived class
}

void A{{class_name}}::Activate()
{
    if (bIsActive) return;

    bIsActive = true;
    OnActivated();
}

void A{{class_name}}::Deactivate()
{
    if (!bIsActive) return;

    bIsActive = false;
    OnDeactivated();
}

void A{{class_name}}::OnBeginPlay()
{
    // Override in derived class for custom BeginPlay logic
}

void A{{class_name}}::OnUpdate(float DeltaTime)
{
    // Override in derived class for custom Tick logic
}
