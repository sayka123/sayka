import SwiftUI

private struct DemoStory: Identifiable {
    let id: Int
    let name: String
    let initials: String
    let title: String
    let colors: [Color]

    static let examples = [
        DemoStory(id: 0, name: "Ada", initials: "A", title: "Yeni bir rota, yeni bir gün", colors: [.purple, .pink]),
        DemoStory(id: 1, name: "Deniz", initials: "D", title: "Kahve molası ☕️", colors: [.blue, .teal]),
        DemoStory(id: 2, name: "Mert", initials: "M", title: "Yoldan bir manzara", colors: [.orange, .red]),
        DemoStory(id: 3, name: "Ece", initials: "E", title: "Günün küçük mutluluğu", colors: [.green, .mint])
    ]
}

struct StoryStripView: View {
    @State private var selectedStory: Int?

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 16) {
                ForEach(DemoStory.examples) { story in
                    Button {
                        selectedStory = story.id
                    } label: {
                        VStack(spacing: 6) {
                            Text(story.initials)
                                .font(.title2.bold())
                                .foregroundStyle(.white)
                                .frame(width: 58, height: 58)
                                .background(LinearGradient(colors: story.colors, startPoint: .topLeading, endPoint: .bottomTrailing))
                                .clipShape(Circle())
                                .padding(3)
                                .overlay(Circle().stroke(.pink, lineWidth: 2))
                            Text(story.name).font(.caption)
                        }
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("\(story.name) adlı örnek hikâyeyi aç")
                }
            }
            .padding(.horizontal, 12)
        }
        .frame(height: 88)
        .fullScreenCover(isPresented: Binding(
            get: { selectedStory != nil },
            set: { if !$0 { selectedStory = nil } }
        )) {
            if let selectedStory {
                StoryViewer(initialIndex: selectedStory) {
                    self.selectedStory = nil
                }
            }
        }
    }
}

private struct StoryViewer: View {
    @State private var page: Int
    let close: () -> Void

    init(initialIndex: Int, close: @escaping () -> Void) {
        _page = State(initialValue: initialIndex)
        self.close = close
    }

    var body: some View {
        TabView(selection: $page) {
            ForEach(DemoStory.examples) { story in
                ZStack(alignment: .top) {
                    LinearGradient(colors: story.colors, startPoint: .topLeading, endPoint: .bottomTrailing)
                        .ignoresSafeArea()
                    VStack(alignment: .leading, spacing: 22) {
                        HStack(spacing: 4) {
                            ForEach(DemoStory.examples) { item in
                                Capsule()
                                    .fill(item.id <= page ? .white : .white.opacity(0.4))
                                    .frame(height: 3)
                            }
                        }
                        HStack {
                            Text("\(story.initials)  \(story.name)").font(.headline)
                            Spacer()
                            Button(action: close) {
                                Image(systemName: "xmark.circle.fill").font(.title2)
                            }
                            .accessibilityLabel("Hikâyeleri kapat")
                        }
                        Spacer()
                        Text(story.title)
                            .font(.largeTitle.bold())
                            .multilineTextAlignment(.leading)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        Spacer()
                        Text("Örnek içerik · Instagram hesabına bağlı değil")
                            .font(.footnote)
                            .frame(maxWidth: .infinity, alignment: .center)
                    }
                    .foregroundStyle(.white)
                    .padding(20)
                }
                .tag(story.id)
            }
        }
        .tabViewStyle(.page(indexDisplayMode: .never))
        .background(.black)
    }
}
