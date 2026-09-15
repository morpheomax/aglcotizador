from streamlit.testing.v1 import AppTest


def test_room_can_be_saved_calculated_and_deleted_without_grid_workflow() -> None:
    app = AppTest.from_file("app.py").run(timeout=20)
    assert not app.exception
    checkbox_labels = [checkbox.label for checkbox in app.checkbox]
    assert "Incluir esta sala en el cálculo, los totales y el BOM de la cotización" in checkbox_labels
    assert "Incluir" not in checkbox_labels

    save_buttons = [button for button in app.button if button.label == "Guardar y calcular esta sala"]
    save_buttons[0].click()
    app.run(timeout=20)

    assert not app.exception
    assert any(metric.label == "Agente" and "kg" in metric.value for metric in app.metric)

    delete_buttons = [button for button in app.button if button.label == "Eliminar esta sala"]
    initial_count = len(delete_buttons)
    delete_buttons[0].click()
    app.run(timeout=20)

    assert not app.exception
    assert len([button for button in app.button if button.label == "Eliminar esta sala"]) == initial_count - 1
