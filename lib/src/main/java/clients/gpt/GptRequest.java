package clients.gpt;

import java.util.ArrayList;
import java.util.List;

import clients.LlmModels;

public class GptRequest {

	private String model;
	private List<Message> messages;
	private int temperature;

	public GptRequest() {
		this.messages = new ArrayList<Message>();
	}

	public String getModel() {
		return model;
	}

	public void setModel(LlmModels model) {
		this.model = model.getRealName();
	}

	public List<Message> getMessages() {
		return messages;
	}

	public void setMessages(List<Message> messages) {
		this.messages = messages;
	}

	public void addMessage(Message message) {
		this.messages.add(message);
	}

	public int getTemperature() {
		return temperature;
	}

	public void setTemperature(int temperature) {
		this.temperature = temperature;
	}
}
