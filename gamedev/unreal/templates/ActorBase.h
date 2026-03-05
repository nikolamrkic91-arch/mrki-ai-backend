// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "{{class_name}}.generated.h"

UCLASS()
class {{api_macro}} A{{class_name}} : public AActor
{
    GENERATED_BODY()

public:
    // Sets default values for this actor's properties
    A{{class_name}}();

protected:
    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

    // Called when this actor is destroyed
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

public:
    // Called every frame
    virtual void Tick(float DeltaTime) override;

    // Components
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    TObjectPtr<USceneComponent> DefaultSceneRoot;

    // Properties
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
    bool bAutoActivate = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
    float TickInterval = 0.0f;

    // Events
    UFUNCTION(BlueprintNativeEvent, Category = "Events")
    void OnActivated();
    virtual void OnActivated_Implementation();

    UFUNCTION(BlueprintNativeEvent, Category = "Events")
    void OnDeactivated();
    virtual void OnDeactivated_Implementation();

    // Public API
    UFUNCTION(BlueprintCallable, Category = "API")
    void Activate();

    UFUNCTION(BlueprintCallable, Category = "API")
    void Deactivate();

    UFUNCTION(BlueprintPure, Category = "API")
    bool IsActive() const { return bIsActive; }

protected:
    UPROPERTY(BlueprintReadOnly, Category = "State")
    bool bIsActive = false;

    // Internal methods
    virtual void OnBeginPlay();
    virtual void OnUpdate(float DeltaTime);
};
