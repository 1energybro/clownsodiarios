# ARCHIVO: streamlit_dof_standalone.py

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Configuración de la página
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    body, .stApp {
        background: #0f1816 !important;
        font-family: 'Share Tech Mono', 'Consolas', monospace !important;
        color: #00ff41;
    }
    .header-card {
        background: linear-gradient(135deg, #0f1816 80%, #1a2d1a 100%);
        border-radius: 12px;
        border: 2px solid #00ff41;
        box-shadow: 0 2px 12px #00ff4133;
        padding: 22px;
        margin: 14px 0;
        font-family: 'Share Tech Mono', 'Consolas', monospace;
        color: #00ff41;
        letter-spacing: 1px;
    }
    .classification-success {
        background: #1a2d1a;
        color: #00ff41;
        border: 2px dashed #00ff41;
        border-radius: 7px;
        font-family: 'Share Tech Mono', 'Consolas', monospace;
        font-size: 1.1em;
        letter-spacing: 1px;
    }
    .stats-card {
        background: #0f1816;
        border: 2px solid #00ff41;
        border-radius: 10px;
        color: #00ff41;
        font-family: 'Share Tech Mono', 'Consolas', monospace;
    }
    .frequency-badge {
        background: #00ff41;
        color: #0f1816;
        border-radius: 14px;
        padding: 4px 12px;
        font-size: 14px;
        font-weight: bold;
        font-family: 'Share Tech Mono', 'Consolas', monospace;
        border: 1.5px solid #00ff41;
        box-shadow: 1px 1px 2px #00ff4133;
        letter-spacing: 1px;
    }
    .stButton>button {
        background: #00ff41 !important;
        color: #0f1816 !important;
        border-radius: 8px !important;
        border: 2px solid #00ff41 !important;
        font-family: 'Share Tech Mono', 'Consolas', monospace !important;
        font-size: 1.1em !important;
        box-shadow: 1px 1px 6px #00ff4133;
        letter-spacing: 1px;
        transition: background 0.2s;
    }
    .stButton>button:hover {
        background: #1a2d1a !important;
        color: #00ff41 !important;
        border: 2px solid #00ff41 !important;
    }
    .stMetric {
        background: #0f1816;
        border-radius: 8px;
        border: 1.5px solid #00ff41;
        color: #00ff41;
        font-family: 'Share Tech Mono', 'Consolas', monospace;
    }
    .stProgress > div > div > div > div {
        background-color: #00ff41 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Share Tech Mono', 'Consolas', monospace !important;
        color: #00ff41 !important;
        text-shadow: 0 0 8px #00ff41cc;
        letter-spacing: 2px;
    }
    .stSidebar {
        background: #1a2d1a !important;
        color: #00ff41 !important;
        font-family: 'Share Tech Mono', 'Consolas', monospace !important;
    }
    .stInfo, .stAlert, .stWarning {
        background: #1a2d1a !important;
        color: #00ff41 !important;
        border: 1.5px solid #00ff41 !important;
        font-family: 'Share Tech Mono', 'Consolas', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitDOFClassifier:
    def __init__(self, db_path="dof_headers.db"):
        # Buscar la base de datos en múltiples ubicaciones
        possible_paths = [
            db_path,
            os.path.join(os.getcwd(), db_path),
            os.path.join(os.path.dirname(__file__), db_path),
            os.path.join(r"C:\Users\userfinal\Downloads\DOF compilado", db_path)
        ]
        
        self.db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.db_path = path
                break
        
        if not self.db_path:
            st.error(f"❌ No se encuentra la base de datos. Buscado en: {possible_paths}")
            st.stop()
        
        st.success(f"✅ Base de datos encontrada: {self.db_path}")
        
        self.categories = {
            'DEPENDENCIA': {
                'label': '🏛️ Dependencia Gubernamental',
                'description': 'Secretarías, institutos, tribunales, bancos centrales, etc.',
                'subcategories': [
                    'SECRETARIA_ESTADO',
                    'ORGANISMO_DESCENTRALIZADO', 
                    'TRIBUNAL',
                    'BANCO_CENTRAL',
                    'INSTITUTO_AUTONOMO',
                    'COMISION_REGULADORA',
                    'OTRO_DEPENDENCIA'
                ]
            },
            'EDITORIAL': {
                'label': '📰 Sección Editorial',
                'description': 'Avisos, convocatorias, edictos, licitaciones, etc.',
                'subcategories': [
                    'AVISOS_GENERALES',
                    'CONVOCATORIAS',
                    'EDICTOS_JUDICIALES',
                    'LICITACIONES',
                    'NOTIFICACIONES',
                    'EXTRACTOS',
                    'OTRO_EDITORIAL'
                ]
            },
            'MIXTO': {
                'label': '🔄 Mixto',
                'description': 'Encabezados que pueden ser tanto dependencia como editorial',
                'subcategories': []
            }
        }
    
    def get_statistics(self):
        """Obtiene estadísticas actuales"""
        conn = sqlite3.connect(self.db_path)
        
        # Verificar que existe la tabla headers
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='headers'")
            if not cursor.fetchone():
                st.error("❌ La tabla 'headers' no existe en la base de datos")
                conn.close()
                return None
        except Exception as e:
            st.error(f"❌ Error accediendo a la base de datos: {e}")
            conn.close()
            return None
        
        # Estadísticas generales
        stats_query = '''
            SELECT 
                CASE 
                    WHEN category IS NULL AND is_valid = 1 THEN 'Sin Clasificar'
                    WHEN is_valid = 0 THEN 'Descartados'
                    WHEN category = 'DEPENDENCIA' THEN 'Dependencias'
                    WHEN category = 'EDITORIAL' THEN 'Editoriales'
                    WHEN category = 'MIXTO' THEN 'Mixtos'
                    ELSE 'Otros'
                END as categoria,
                COUNT(*) as cantidad,
                SUM(frequency) as apariciones
            FROM headers
            GROUP BY categoria
            ORDER BY apariciones DESC
        '''
        
        try:
            stats_df = pd.read_sql_query(stats_query, conn)
        except Exception as e:
            st.error(f"❌ Error ejecutando consulta de estadísticas: {e}")
            conn.close()
            return None
        
        # Progreso general
        total_query = "SELECT COUNT(*) as total FROM headers WHERE is_valid = 1"
        try:
            total_df = pd.read_sql_query(total_query, conn)
            total_headers = total_df['total'].iloc[0]
        except Exception as e:
            st.error(f"❌ Error obteniendo total: {e}")
            conn.close()
            return None
        
        sin_clasificar = stats_df[stats_df['categoria'] == 'Sin Clasificar']['cantidad'].sum() if 'Sin Clasificar' in stats_df['categoria'].values else 0
        clasificados = total_headers - sin_clasificar
        
        conn.close()
        
        return {
            'stats': stats_df,
            'total': total_headers,
            'clasificados': clasificados,
            'sin_clasificar': sin_clasificar,
            'progreso': (clasificados / total_headers * 100) if total_headers > 0 else 0
        }
    
    def get_unclassified_batch(self, start_idx=0, batch_size=5):
        """Obtiene un lote de encabezados sin clasificar"""
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query('''
                SELECT id, cleaned_text, frequency, original_text
                FROM headers 
                WHERE category IS NULL AND is_valid = 1
                ORDER BY frequency DESC, LENGTH(cleaned_text) ASC
                LIMIT ? OFFSET ?
            ''', conn, params=(batch_size, start_idx))
        except Exception as e:
            st.error(f"❌ Error obteniendo lote: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()
        return df
    
    def classify_header(self, header_id, category, subcategory=None, notes=None):
        """Clasifica un encabezado"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE headers 
                SET category = ?, subcategory = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (category, subcategory, notes, header_id))
            conn.commit()
            return True
        except Exception as e:
            st.error(f"❌ Error clasificando encabezado: {e}")
            return False
        finally:
            conn.close()
    
    def mark_as_invalid(self, header_id):
        """Marca un encabezado como inválido"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE headers SET is_valid = 0 WHERE id = ?", (header_id,))
            conn.commit()
            return True
        except Exception as e:
            st.error(f"❌ Error marcando como inválido: {e}")
            return False
        finally:
            conn.close()
    
    def export_catalog(self, filename):
        """Exporta el catálogo final"""
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query('''
                SELECT 
                    id,
                    original_text,
                    cleaned_text,
                    frequency,
                    COALESCE(category, 'SIN_CLASIFICAR') as category,
                    subcategory,
                    is_valid,
                    notes,
                    created_at,
                    updated_at
                FROM headers 
                ORDER BY 
                    CASE WHEN category IS NULL THEN 1 ELSE 0 END,
                    frequency DESC, 
                    category, 
                    cleaned_text
            ''', conn)
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            return len(df)
        except Exception as e:
            st.error(f"❌ Error exportando: {e}")
            return 0
        finally:
            conn.close()

def main():
    # Inicializar clasificador
    if 'classifier' not in st.session_state:
        try:
            st.session_state.classifier = StreamlitDOFClassifier()
        except Exception as e:
            st.error(f"❌ Error inicializando clasificador: {e}")
            st.stop()
    
    if 'current_batch_start' not in st.session_state:
        st.session_state.current_batch_start = 0
    
    if 'batch_size' not in st.session_state:
        st.session_state.batch_size = 5
    
    classifier = st.session_state.classifier
    
    # Título principal
    st.title("🏛️ Clasificador de Encabezados del DOF")
    st.markdown("### Sistema de clasificación para el Diario Oficial de la Federación")
    
    # Obtener estadísticas
    stats = classifier.get_statistics()
    if not stats:
        st.error("❌ No se pudieron obtener las estadísticas")
        st.stop()
    
    # Sidebar con estadísticas
    with st.sidebar:
        st.header("📊 Estadísticas")
        
        # Información de la base de datos
        st.info(f"📁 BD: {os.path.basename(classifier.db_path)}")
        
        # Métricas principales
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", stats['total'])
            st.metric("Clasificados", stats['clasificados'])
        with col2:
            st.metric("Pendientes", stats['sin_clasificar'])
            st.metric("Progreso", f"{stats['progreso']:.1f}%")
        
        # Barra de progreso
        progress_bar = st.progress(stats['progreso'] / 100)
        
        # Gráfico de distribución
        if not stats['stats'].empty:
            fig = px.pie(
                stats['stats'], 
                values='cantidad', 
                names='categoria',
                title="Distribución por Categoría"
            )
            fig.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        # Configuración
        st.header("⚙️ Configuración")
        batch_size = st.selectbox("Encabezados por lote", [3, 5, 10], index=1)
        st.session_state.batch_size = batch_size
    
    # Área principal
    if stats['sin_clasificar'] == 0:
        st.success("🎉 ¡Felicidades! Todos los encabezados han sido clasificados.")
        
        # Botón para exportar resultados finales
        if st.button("📊 Exportar Catálogo Final"):
            filename = f"catalogo_dof_final_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            count = classifier.export_catalog(filename)
            if count > 0:
                st.success(f"✅ Catálogo exportado: {filename} ({count} registros)")
            
                # Mostrar resumen final
                st.header("📋 Resumen Final")
                final_stats = stats['stats']
                st.dataframe(final_stats, use_container_width=True)
    
    else:
        # Obtener lote actual
        current_batch = classifier.get_unclassified_batch(
            st.session_state.current_batch_start, 
            st.session_state.batch_size
        )
        
        if current_batch.empty:
            st.warning("No hay más encabezados para clasificar en este lote.")
            if st.button("🔄 Reiniciar desde el principio"):
                st.session_state.current_batch_start = 0
                st.rerun()
        
        else:
            # Navegación de lotes
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("⬅️ Lote Anterior") and st.session_state.current_batch_start > 0:
                    st.session_state.current_batch_start -= st.session_state.batch_size
                    st.rerun()
            
            with col2:
                lote_actual = (st.session_state.current_batch_start // st.session_state.batch_size) + 1
                total_lotes = (stats['sin_clasificar'] + st.session_state.batch_size - 1) // st.session_state.batch_size
                st.markdown(f"<h3 style='text-align: center'>Lote {lote_actual} de {total_lotes}</h3>", unsafe_allow_html=True)
            
            with col3:
                if st.button("➡️ Lote Siguiente"):
                    st.session_state.current_batch_start += st.session_state.batch_size
                    st.rerun()
            
            st.markdown("---")
            
            # Mostrar algunos ejemplos de los encabezados en este lote
            st.markdown("### 👀 Vista previa de este lote:")
            preview_text = " | ".join([f"**{row['cleaned_text']}** ({row['frequency']}x)" for _, row in current_batch.iterrows()])
            st.markdown(preview_text)
            st.markdown("---")
            
            # Procesar cada encabezado del lote
            for idx, row in current_batch.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="header-card">
                        <h4>📄 Encabezado #{row['id']} 
                            <span class="frequency-badge">Aparece {row['frequency']} veces</span>
                        </h4>
                        <p><strong>Texto:</strong> {row['cleaned_text']}</p>
                        {"<p><strong>Original:</strong> " + row['original_text'] + "</p>" if row['original_text'] != row['cleaned_text'] else ""}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Opciones de clasificación
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Selector de categoría
                        category_options = ['Seleccionar...'] + list(classifier.categories.keys()) + ['❌ DESCARTAR']
                        category_labels = ['Seleccionar...'] + [classifier.categories[cat]['label'] for cat in classifier.categories.keys()] + ['❌ Descartar este encabezado']
                        
                        selected_category = st.selectbox(
                            f"Categoría para #{row['id']}:",
                            options=category_options,
                            format_func=lambda x: category_labels[category_options.index(x)],
                            key=f"cat_{row['id']}"
                        )
                        
                        # Mostrar descripción de la categoría
                        if selected_category in classifier.categories:
                            st.info(f"ℹ️ {classifier.categories[selected_category]['description']}")
                        
                        # Selector de subcategoría si aplica
                        subcategory = None
                        if selected_category in classifier.categories and classifier.categories[selected_category]['subcategories']:
                            subcategory_options = ['Sin subcategoría'] + classifier.categories[selected_category]['subcategories']
                            subcategory = st.selectbox(
                                f"Subcategoría:",
                                options=subcategory_options,
                                key=f"subcat_{row['id']}"
                            )
                            subcategory = subcategory if subcategory != 'Sin subcategoría' else None
                        
                        # Campo de notas
                        notes = st.text_input(f"Notas opcionales:", key=f"notes_{row['id']}")
                    
                    with col2:
                        st.markdown("<br><br>", unsafe_allow_html=True)  # Espaciado
                        
                        # Botón de clasificar
                        if st.button(f"✅ Clasificar #{row['id']}", key=f"classify_{row['id']}", type="primary"):
                            if selected_category == 'Seleccionar...':
                                st.error("❌ Por favor selecciona una categoría")
                            elif selected_category == '❌ DESCARTAR':
                                if classifier.mark_as_invalid(row['id']):
                                    st.success(f"❌ Encabezado #{row['id']} descartado")
                                    st.rerun()
                            else:
                                if classifier.classify_header(
                                    row['id'], 
                                    selected_category, 
                                    subcategory, 
                                    notes if notes else None
                                ):
                                    st.markdown("""
                                    <div class="classification-success">
                                        ✅ ¡Encabezado clasificado exitosamente!
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.rerun()
                    
                    st.markdown("---")
            
            # Botones de acción masiva
            st.markdown("### 🚀 Acciones Rápidas")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Actualizar Estadísticas"):
                    st.rerun()
            
            with col2:
                if st.button("💾 Exportar Progreso"):
                    filename = f"progreso_dof_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                    count = classifier.export_catalog(filename)
                    if count > 0:
                        st.success(f"✅ Progreso exportado: {filename} ({count} registros)")
            
            with col3:
                if st.button("⏭️ Saltar Lote"):
                    st.session_state.current_batch_start += st.session_state.batch_size
                    st.rerun()

if __name__ == "__main__":
    main()
