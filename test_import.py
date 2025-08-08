try:
    import model_service
    print('model_service imported successfully')
except Exception as e:
    print(f'Error importing model_service: {e}')
    import traceback
    traceback.print_exc()